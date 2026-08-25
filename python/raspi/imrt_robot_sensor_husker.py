# IMRT100 robot code with short-term turn memory

import imrt_robot_serial
import time
import sys


execution_frequency = 10
execution_period = 1.0 / execution_frequency

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyACM0")
except Exception:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()

motor_serial.run()

turn_until = 0.0
turn_duration = 1.34
last_turn_direction = 0

print("Entering loop. Ctrl+c to terminate")
while not motor_serial.shutdown_now:
    iteration_start_time = time.time()
    now = time.time()
    obstacle_threshold_cm = 15.0

    dist_1 = motor_serial.get_dist_1()
    dist_2 = motor_serial.get_dist_2()
    dist_3 = motor_serial.get_dist_3()
    dist_4 = motor_serial.get_dist_4()
    print("foran:", dist_1, "venstre:", dist_2, "hoyre:", dist_3, "bak:", dist_4)

    speed_motor_1 = 120
    speed_motor_2 = 120

    if now < turn_until:
        if last_turn_direction < 0:
            speed_motor_1 = -60
            speed_motor_2 = 60
        else:
            speed_motor_1 = 60
            speed_motor_2 = -60

    elif dist_1 < obstacle_threshold_cm and dist_2 < 30.0 and dist_3 < 30.0:
        turn_until = now + turn_duration
        if last_turn_direction >= 0:
            speed_motor_1 = -60
            speed_motor_2 = 60
            last_turn_direction = -1
        else:
            speed_motor_1 = 60
            speed_motor_2 = -60
            last_turn_direction = 1

    elif dist_1 < obstacle_threshold_cm:
        if dist_2 > dist_3:
            speed_motor_1 = -80
            speed_motor_2 = 120
            last_turn_direction = -1
        else:
            speed_motor_1 = 120
            speed_motor_2 = -80
            last_turn_direction = 1

    elif dist_2 < obstacle_threshold_cm and dist_2 < dist_3:
        speed_motor_1 = 120
        speed_motor_2 = -80
        last_turn_direction = 1

    elif dist_3 < obstacle_threshold_cm:
        speed_motor_1 = -80
        speed_motor_2 = 120
        last_turn_direction = -1

    speed_motor_1 = max(-400, min(400, speed_motor_1))
    speed_motor_2 = max(-400, min(400, speed_motor_2))
    motor_serial.send_command(speed_motor_1, speed_motor_2)

    iteration_duration = time.time() - iteration_start_time
    if iteration_duration < execution_period:
        time.sleep(execution_period - iteration_duration)

print("Goodbye")
