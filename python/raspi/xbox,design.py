import math
import sys
import time

import imrt_robot_serial


# ------------------------------------------------------------
# Innstillinger
# ------------------------------------------------------------

SERIAL_PORT = "/dev/ttyACM0"

EXECUTION_FREQUENCY_HZ = 10
EXECUTION_PERIOD = 1.0 / EXECUTION_FREQUENCY_HZ

MAX_MOTOR_SPEED = 400

NORMAL_SPEED = 120
SLOW_SPEED = 60
TURN_OUTER_SPEED = 120
TURN_INNER_SPEED = -80
ROTATION_SPEED = 60

OBSTACLE_DISTANCE_CM = 15.0
SLOW_DISTANCE_CM = 30.0
SIDE_BLOCKED_DISTANCE_CM = 30.0

# Må kalibreres på den faktiske roboten
TURN_AROUND_DURATION = 1.34


def clamp_motor_speed(speed):
    """Begrenser motorhastigheten til gyldig område."""
    return max(-MAX_MOTOR_SPEED, min(MAX_MOTOR_SPEED, int(speed)))


def valid_distance(distance):
    """Kontrollerer at en sensorverdi kan brukes."""
    return (
        isinstance(distance, (int, float))
        and math.isfinite(distance)
        and distance >= 0
    )


def stop_robot(robot):
    """Forsøker å stoppe begge motorene."""
    try:
        robot.send_command(0, 0)
    except Exception:
        pass


# ------------------------------------------------------------
# Oppkobling
# ------------------------------------------------------------

motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect(SERIAL_PORT)
except Exception as error:
    print(f"Kunne ikke åpne {SERIAL_PORT}: {error}")
    print("Er roboten koblet til?")
    sys.exit(1)

try:
    motor_serial.run()
except Exception as error:
    print(f"Kunne ikke starte mottak av sensordata: {error}")
    stop_robot(motor_serial)
    sys.exit(1)


# Tidspunktet en eventuell helomvending skal avsluttes
turn_until = 0.0

# 1 betyr rotasjon mot høyre, -1 betyr rotasjon mot venstre
turn_direction = 1


print("Programmet kjører. Trykk Ctrl+C for å avslutte.")

try:
    while not motor_serial.shutdown_now:
        iteration_start = time.monotonic()
        now = iteration_start

        # ----------------------------------------------------
        # Les sensorene
        # ----------------------------------------------------

        try:
            front_distance = motor_serial.get_dist_1()
            left_distance = motor_serial.get_dist_2()
            right_distance = motor_serial.get_dist_3()
            rear_distance = motor_serial.get_dist_4()
        except Exception as error:
            print(f"Feil ved lesing av sensorer: {error}")
            stop_robot(motor_serial)
            time.sleep(EXECUTION_PERIOD)
            continue

        distances = (
            front_distance,
            left_distance,
            right_distance,
            rear_distance,
        )

        # Stopp hvis en eller flere sensorverdier er ugyldige.
        if not all(valid_distance(distance) for distance in distances):
            print(f"Ugyldige sensorverdier: {distances}")
            stop_robot(motor_serial)
            time.sleep(EXECUTION_PERIOD)
            continue

        print(
            f"Foran: {front_distance:6.1f} cm | "
            f"Venstre: {left_distance:6.1f} cm | "
            f"Høyre: {right_distance:6.1f} cm | "
            f"Bak: {rear_distance:6.1f} cm"
        )

        # Normal kjøring rett fram
        speed_motor_1 = NORMAL_SPEED
        speed_motor_2 = NORMAL_SPEED

        front_blocked = front_distance < OBSTACLE_DISTANCE_CM
        left_blocked = left_distance < OBSTACLE_DISTANCE_CM
        right_blocked = right_distance < OBSTACLE_DISTANCE_CM

        confined_in_front = (
            front_blocked
            and left_distance < SIDE_BLOCKED_DISTANCE_CM
            and right_distance < SIDE_BLOCKED_DISTANCE_CM
        )

        # ----------------------------------------------------
        # Bestem motorhastigheter
        # ----------------------------------------------------

        if now < turn_until:
            # Fortsett en helomvending som allerede er startet.
            speed_motor_1 = ROTATION_SPEED * turn_direction
            speed_motor_2 = -ROTATION_SPEED * turn_direction

        elif confined_in_front:
            # Lite plass foran og på begge sider.
            # Roter mot siden med mest ledig plass.
            if right_distance > left_distance:
                turn_direction = 1
            else:
                turn_direction = -1

            turn_until = now + TURN_AROUND_DURATION

            speed_motor_1 = ROTATION_SPEED * turn_direction
            speed_motor_2 = -ROTATION_SPEED * turn_direction

        elif front_blocked:
            # Hindring rett foran: sving mot siden med mest plass.
            if left_distance > right_distance:
                # Sving mot venstre
                speed_motor_1 = -TURN_INNER_SPEED
                speed_motor_2 = -TURN_OUTER_SPEED
            else:
                # Sving mot høyre
                speed_motor_1 = TURN_OUTER_SPEED
                speed_motor_2 = TURN_INNER_SPEED

        elif left_blocked:
            # Hindring på venstre side: sving mot høyre.
            speed_motor_1 = TURN_OUTER_SPEED
            speed_motor_2 = TURN_INNER_SPEED

        elif right_blocked:
            # Hindring på høyre side: sving mot venstre.
            speed_motor_1 = -TURN_INNER_SPEED
            speed_motor_2 = -TURN_OUTER_SPEED

        elif front_distance < SLOW_DISTANCE_CM:
            # Hindring foran, men ikke akutt nær.
            speed_motor_1 = SLOW_SPEED
            speed_motor_2 = SLOW_SPEED

        # ----------------------------------------------------
        # Send kommandoen
        # ----------------------------------------------------

        speed_motor_1 = clamp_motor_speed(speed_motor_1)
        speed_motor_2 = clamp_motor_speed(speed_motor_2)

        motor_serial.send_command(speed_motor_1, speed_motor_2)

        # Hold løkkefrekvensen på omtrent 10 Hz.
        iteration_duration = time.monotonic() - iteration_start
        remaining_time = EXECUTION_PERIOD - iteration_duration

        if remaining_time > 0:
            time.sleep(remaining_time)

except KeyboardInterrupt:
    print("\nProgrammet ble stoppet av brukeren.")

except Exception as error:
    print(f"\nUventet feil: {error}")

finally:
    stop_robot(motor_serial)
    print("Motorene er stoppet. Goodbye.")