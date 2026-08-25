# IMRT100 robot sensor program.

import sys
import time

import imrt_robot_serial


# Send commands at 10 Hz.
execution_frequency = 10
execution_period = 1.0 / execution_frequency


# Create the motor serial object.
motor_serial = imrt_robot_serial.IMRTRobotSerial()


# Open the serial port. Exit if it cannot be opened.
try:
    motor_serial.connect("/dev/ttyACM0")
except Exception:
    print("Could not open port. Is your robot connected?\nExiting program")
    sys.exit()


# Start the serial receive thread.
motor_serial.run()

# Keep turning until this time.
turn_until = 0.0
turn_duration = 1.34


print("Entering loop. Ctrl+c to terminate")
while not motor_serial.shutdown_now:
    iteration_start_time = time.time()
    now = time.time()

    obstacle_threshold_cm = 30.0

    # Read the distance sensors.
    dist_1 = motor_serial.get_dist_1()
    dist_2 = motor_serial.get_dist_2()
    dist_3 = motor_serial.get_dist_3()
    dist_4 = motor_serial.get_dist_4()
    print(
        "foran:", dist_1,
        "venstre:", dist_2,
        "hoyre:", dist_3,
        "bak:", dist_4,
    )

    # Default: drive forward.
    speed_motor_1 = 120
    speed_motor_2 = 120

    # Continue turning for the remaining duration.
    if now < turn_until:
        speed_motor_1 = 60
        speed_motor_2 = -60

    # Obstacle in front and on both sides.
    elif (
        dist_1 < obstacle_threshold_cm
        and dist_2 < obstacle_threshold_cm
        and dist_3 < obstacle_threshold_cm
    ):
        turn_until = now + turn_duration
        speed_motor_1 = 60
        speed_motor_2 = -60

    # Obstacle straight ahead: choose the side with more space.
    elif dist_1 < obstacle_threshold_cm:
        if dist_2 > dist_3:
            speed_motor_1 = -80
            speed_motor_2 = 120
        else:
            speed_motor_1 = 120
            speed_motor_2 = -80

    # Obstacle on the left: turn right.
    elif dist_2 < obstacle_threshold_cm and dist_2 < dist_3:
        speed_motor_1 = 120
        speed_motor_2 = -80

    # Obstacle on the right: turn left.
    elif dist_3 < obstacle_threshold_cm:
        speed_motor_1 = -80
        speed_motor_2 = 120

    # Obstacle is still far away.
    elif dist_1 > obstacle_threshold_cm and dist_2 == dist_3:
        speed_motor_1 = 60
        speed_motor_2 = 60

    # Keep motor commands in the valid range.
    speed_motor_1 = max(-400, min(400, speed_motor_1))
    speed_motor_2 = max(-400, min(400, speed_motor_2))

    # Send commands to the motors.
    motor_serial.send_command(speed_motor_1, speed_motor_2)

    # Keep the loop at the selected frequency.
    iteration_duration = time.time() - iteration_start_time
    if iteration_duration < execution_period:
        time.sleep(execution_period - iteration_duration)


print("Goodbye")
