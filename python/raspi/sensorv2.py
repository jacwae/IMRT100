import imrt_robot_serial
import time
import sys

# Programmet sender 10 kommandoer i sekundet
execution_frequency = 10
execution_period = 1.0 / execution_frequency

# Avstand der roboten reagerer på hindringer
obstacle_threshold_cm = 15.0

# Tid roboten skal snu når den er blokkert
turn_duration = 0.84
turn_until = 0.0

# Opprett forbindelse med roboten
motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyACM0")
except Exception:
    print("Kunne ikke koble til roboten. Sjekk at den er koblet til.")
    sys.exit()

# Start mottak av sensordata
motor_serial.run()

print("Starter roboten. Trykk Ctrl+C for å stoppe.")

try:
    while not motor_serial.shutdown_now:
        iteration_start_time = time.time()
        now = time.time()

        # Les sensorene
        dist_1 = motor_serial.get_dist_1()  # foran
        dist_2 = motor_serial.get_dist_2()  # høyre
        dist_3 = motor_serial.get_dist_3()  # venstre
        dist_4 = motor_serial.get_dist_4()  # bak

        print(
            "Foran:", dist_1,
            "Høyre:", dist_2,
            "Venstre:", dist_3,
            "Bak:", dist_4
        )

        # Standard: kjør framover
        speed_motor_1 = 120
        speed_motor_2 = 120

        # Fortsett en vending som allerede er startet
        if now < turn_until:
            speed_motor_1 = -60
            speed_motor_2 = 60

        # Hindring foran og lite plass på begge sider:
        # snu rundt
        elif (
            dist_1 < obstacle_threshold_cm
            and dist_2 < 30.0
            and dist_3 < 30.0
        ):
            turn_until = now + turn_duration
            speed_motor_1 = -60
            speed_motor_2 = 60

        # Hindring rett foran:
        # velg siden med mest plass
        elif dist_1 < obstacle_threshold_cm:
            if dist_2 > dist_3:
                # Mest plass til høyre
                speed_motor_1 = -80
                speed_motor_2 = 120
            else:
                # Mest plass til venstre
                speed_motor_1 = 120
                speed_motor_2 = -80

        # Hindring på høyre side, men friere til venstre
        elif (
            dist_2 < obstacle_threshold_cm
            and dist_3 >= obstacle_threshold_cm
        ):
            speed_motor_1 = 120
            speed_motor_2 = -80

        # Hindring på venstre side, men friere til høyre
        elif (
            dist_3 < obstacle_threshold_cm
            and dist_2 >= obstacle_threshold_cm
        ):
            speed_motor_1 = -80
            speed_motor_2 = 120

        # Begrens motorfart mellom -400 og 400
        speed_motor_1 = max(-400, min(400, speed_motor_1))
        speed_motor_2 = max(-400, min(400, speed_motor_2))

        # Send kommando til motorene
        motor_serial.send_command(speed_motor_1, speed_motor_2)

        # Hold løkken på 10 ganger per sekund
        iteration_duration = time.time() - iteration_start_time
        if iteration_duration < execution_period:
            time.sleep(execution_period - iteration_duration)

except KeyboardInterrupt:
    print("Robot stoppet av bruker.")

finally:
    # Stopp motorene når programmet avsluttes
    motor_serial.send_command(0, 0)
    print("Goodbye")