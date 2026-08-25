import imrt_robot_serial
import time
import signal
import sys

# Programmet sender 10 kommandoer i sekundet
execution_frequency = 10
execution_period = 1.0 / execution_frequency

# Avstand der roboten reagerer på hindringer
obstacle_threshold_cm = 20.0

# Tid roboten skal snu når den er blokkert
turn_duration = 1.34
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
        dist_2 = motor_serial.get_dist_2()  # venstre
        dist_3 = motor_serial.get_dist_3()  # høyre 
        dist_4 = motor_serial.get_dist_4()  # bak

        print(
            "Foran:", dist_1,
            "venstre:", dist_2,
            "høyre:", dist_3,
            "Bak:", dist_4
        )

        # default fart roboten skal holde

        motor_speed_1 = 160
        motor_speed_2 = 160

        #fortsette vending som har startet
        if now < turn_until:
            motor_speed_1 = 60
            motor_speed_2 = -60

        elif dist_1 < obstacle_threshold_cm and dist_2 < 30.0 and dist_3 <30.0:
            #snu rundt 
            turn_until = now + turn_duration
            motor_speed_1 = 60
            motor_speed_2 = -60
        # hvis distansen på sensor 1 er mindre enn 15, sving til siden som har største avstand
        elif dist_1 < obstacle_threshold_cm:
            if dist_2< dist_3:
                # sving høyre 
                motor_speed_1 = 120
                motor_speed_2 = -80
            # sving vensrte
            else:
                motor_speed_1 = -80
                motor_speed_2 = 120
        # Hindring på venstre side: sving høyre.
        elif dist_2 < obstacle_threshold_cm:
            motor_speed_1 = 120
            motor_speed_2 = -80

        # Hindring på høyre side: sving venstre.
        elif dist_3 < obstacle_threshold_cm or dist_3 > 50:
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
    # Stopp motorene når programmet avsluttes
    motor_serial.send_command(0, 0)
    print("Goodbye")
           


