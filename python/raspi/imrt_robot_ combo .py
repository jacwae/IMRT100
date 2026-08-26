import imrt_robot_serial
import time
import sys

# Velg scenario:
# "vanlig" = den opprinnelige hindringskoden
# "veggfølging" = følg veggen på høyre side i labyrinten
scenario = "veggfølging"

# Programmet sender 10 kommandoer i sekundet
execution_frequency = 10
execution_period = 1.0 / execution_frequency

# Avstand der roboten reagerer på hindringer
obstacle_threshold_cm = 18.0

# Vanlig scenario: tid roboten snur når den er blokkert
turn_duration = 1.34

# Veggfølgingsscenario:
# Robotens høyre sensor skal helst måle mellom disse verdiene
wall_min_cm = 10.0
wall_max_cm = 25.0

# Juster dette tallet til roboten svinger cirka 90 grader
turn_90_duration = 0.6

turn_until = 0.0
turn_motor_1 = 0
turn_motor_2 = 0

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
        dist_2 = motor_serial.get_dist_2()  # venstre
        dist_3 = motor_serial.get_dist_3()  # høyre
        dist_4 = motor_serial.get_dist_4()  # bak

        print(
            "Foran:", dist_1,
            "Venstre:", dist_2,
            "Høyre:", dist_3,
            "Bak:", dist_4
        )

        # Standard fart
        motor_speed_1 = 160
        motor_speed_2 = 160

        # ---------------- VE G G F Ø L G I N G ----------------
        if scenario == "veggfølging":
            
            # Fortsett en 90-graders sving som allerede har startet
            if now < turn_until:
                motor_speed_1 = turn_motor_1
                motor_speed_2 = turn_motor_2
            elif dist_1 <obstacle_threshold_cm:
            # Stor åpning på høyre side:
            # sving høyre for å følge veggen
                if dist_3 > wall_max_cm:
                    turn_motor_2 = -80
                    turn_motor_1 = 120
                    motor_speed_1 = turn_motor_1
                    motor_speed_2 = turn_motor_2
                    turn_until = now + turn_90_duration

            # Robot er for nær veggen på høyre side:
            # korriger litt mot venstre
                elif dist_3 < wall_min_cm:
                    motor_speed_1 = -80
                    motor_speed_2 = 120

            # Veggen er på riktig avstand:
            # kjør rett fram
                else:
                    motor_speed_1 = 160
                    motor_speed_2 = 160

        # ---------------- V A N L I G   S T Y R I N G ----------------
        else:
            # Fortsett vending som har startet
            if now < turn_until:
                motor_speed_1 = 60
                motor_speed_2 = -60

            # Hindring foran og på begge sider: snu rundt
            elif (
                dist_1 < obstacle_threshold_cm
                and dist_2 < 30.0
                and dist_3 < 30.0
            ):
                turn_until = now + turn_duration
                motor_speed_1 = 60
                motor_speed_2 = -60

            # Hindring foran:
            # sving mot siden med mest plass
            elif dist_1 < obstacle_threshold_cm:
                if dist_2 < dist_3:
                    # Sving høyre
                    motor_speed_1 = 120
                    motor_speed_2 = -80
                else:
                    # Sving venstre
                    motor_speed_1 = -80
                    motor_speed_2 = 120

            # Hindring på venstre side: sving høyre
            elif dist_2 < obstacle_threshold_cm:
                motor_speed_1 = 120
                motor_speed_2 = -80

            # Hindring på høyre side: sving venstre
            elif dist_3 < obstacle_threshold_cm:
                motor_speed_1 = -80
                motor_speed_2 = 120

        # Begrens motorfart mellom -400 og 400
        motor_speed_1 = max(-400, min(400, motor_speed_1))
        motor_speed_2 = max(-400, min(400, motor_speed_2))

        # Send kommando til motorene
        motor_serial.send_command(motor_speed_1, motor_speed_2)

        # Hold løkken på 10 ganger per sekund
        iteration_duration = time.time() - iteration_start_time
        if iteration_duration < execution_period:
            time.sleep(execution_period - iteration_duration)

except KeyboardInterrupt:
    print("Robot stoppet av bruker.")

finally:
    motor_serial.send_command(0, 0)
    print("Goodbye")


