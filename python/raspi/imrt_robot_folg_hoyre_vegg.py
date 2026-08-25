import sys
import time
import statistics

import imrt_robot_serial


LOOP_FREQUENCY = 10
LOOP_PERIOD = 1.0 / LOOP_FREQUENCY

FRONT_STOP_DISTANCE = 30.0
TARGET_RIGHT_DISTANCE = 22.0
RIGHT_OPEN_DISTANCE = 50.0
WALL_FOUND_DISTANCE = 38.0

FORWARD_SPEED = 90
TURN_SPEED = 85
MAX_SPEED = 180
MIN_FORWARD_SPEED = 50
TURN_90_TIME = 0.80
FILTER_SIZE = 3
MAX_INVALID_READS = 5


motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyACM0")
except Exception:
    print("Kunne ikke koble til roboten. Sjekk kabel og port.")
    sys.exit()

motor_serial.run()

front_history = []
right_history = []
last_valid_front = None
last_valid_right = None
invalid_front_reads = 0
invalid_right_reads = 0
# Start med å finne høyreveggen. Ikke ta en høyresving i et åpent område.
right_turn_armed = False


def limit(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def valid_distance(value):
    return 1 <= float(value) <= 255


def stop_robot(duration=0.1):
    motor_serial.send_command(0, 0)
    time.sleep(duration)


def drive(left_speed, right_speed, duration):
    left_speed = limit(left_speed, -MAX_SPEED, MAX_SPEED)
    right_speed = limit(right_speed, -MAX_SPEED, MAX_SPEED)
    end_time = time.time() + duration

    while time.time() < end_time:
        motor_serial.send_command(left_speed, right_speed)
        time.sleep(LOOP_PERIOD)


def read_sensors():
    global last_valid_front, last_valid_right
    global invalid_front_reads, invalid_right_reads

    raw_front = motor_serial.get_dist_1()
    raw_right = motor_serial.get_dist_2()

    if valid_distance(raw_front):
        last_valid_front = float(raw_front)
        invalid_front_reads = 0
    else:
        invalid_front_reads += 1

    if valid_distance(raw_right):
        last_valid_right = float(raw_right)
        invalid_right_reads = 0
    else:
        invalid_right_reads += 1

    if (
        invalid_front_reads >= MAX_INVALID_READS
        or invalid_right_reads >= MAX_INVALID_READS
        or last_valid_front is None
        or last_valid_right is None
    ):
        return None, None

    front_history.append(last_valid_front)
    right_history.append(last_valid_right)

    if len(front_history) > FILTER_SIZE:
        front_history.pop(0)
    if len(right_history) > FILTER_SIZE:
        right_history.pop(0)

    return statistics.median(front_history), statistics.median(right_history)


def reset_sensor_filter():
    front_history.clear()
    right_history.clear()


def turn_left():
    stop_robot()
    # Motor 1 left, motor 2 right: turn left.
    drive(-TURN_SPEED, TURN_SPEED, TURN_90_TIME)
    stop_robot()
    reset_sensor_filter()


def turn_right():
    stop_robot()
    # Motor 1 right, motor 2 left: turn right.
    drive(TURN_SPEED, -TURN_SPEED, TURN_90_TIME)
    stop_robot()
    reset_sensor_filter()


def follow_right_wall(right_distance):
    error = right_distance - TARGET_RIGHT_DISTANCE
    correction = limit(error * 1.5, -35, 35)

    left_speed = limit(FORWARD_SPEED + correction, MIN_FORWARD_SPEED, MAX_SPEED)
    right_speed = limit(FORWARD_SPEED - correction, MIN_FORWARD_SPEED, MAX_SPEED)
    motor_serial.send_command(left_speed, right_speed)


print("Starter høyre-veggfølger. Trykk Ctrl+C for å stoppe.")

try:
    while not motor_serial.shutdown_now:
        loop_start = time.time()
        front_distance, right_distance = read_sensors()

        if front_distance is None:
            print("Sensorfeil: stopper roboten")
            stop_robot(0.2)
            continue

        print(
            "Foran:", round(front_distance, 1),
            "Høyre:", round(right_distance, 1),
        )

        if not right_turn_armed and right_distance < WALL_FOUND_DISTANCE:
            right_turn_armed = True

        # Fronten har alltid prioritet, slik at roboten ikke svinger inn i en vegg.
        if front_distance < FRONT_STOP_DISTANCE:
            stop_robot(0.15)
            turn_left()
            new_front, _ = read_sensors()
            if new_front is not None and new_front < FRONT_STOP_DISTANCE:
                turn_left()
        elif right_turn_armed and right_distance > RIGHT_OPEN_DISTANCE:
            turn_right()
            right_turn_armed = False
            drive(FORWARD_SPEED, FORWARD_SPEED, 0.15)
        elif not right_turn_armed and right_distance > WALL_FOUND_DISTANCE:
            motor_serial.send_command(FORWARD_SPEED, FORWARD_SPEED)
        else:
            follow_right_wall(right_distance)

        elapsed = time.time() - loop_start
        if elapsed < LOOP_PERIOD:
            time.sleep(LOOP_PERIOD - elapsed)

except KeyboardInterrupt:
    print("Robot stoppet av bruker.")
finally:
    motor_serial.send_command(0, 0)
    print("Goodbye")
