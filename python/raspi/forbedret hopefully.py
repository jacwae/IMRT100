import imrt_robot_serial
import time
import signal
import sys
from pathlib import Path
import random
import subprocess


# Lydfilen ligger i samme mappe som Python-programmet
AUDIO_FILE = Path(__file__).with_name("dinosaur.wav")


def play_audio(file_path):
    """Spiller en WAV-fil."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fant ikke lydfilen: {file_path}")

    print(f"Spiller: {file_path.name}")
    return subprocess.Popen(["aplay", "-q", str(file_path)])


next_audio_time = time.time() + random.uniform(3, 5)
audio_process = None


# Programmet sender 10 kommandoer i sekundet
execution_frequency = 10
execution_period = 1.0 / execution_frequency

# Avstand der roboten reagerer på hindringer
obstacle_threshold_cm = 20.0
right_open = 35
side_margin = 4
# Tid roboten skal snu når den er blokkert
turn_duration = 1.34
turn_duration_90 = 0.20
turn_until = 0.0
turn_speed_1 = 0
turn_speed_2 = 0

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

        # Spill av lyd tilfeldig hvert 3.-5. sekund uten å stoppe roboten.
        if now >= next_audio_time:
            if audio_process is None or audio_process.poll() is not None:
                try:
                    audio_process = play_audio(AUDIO_FILE)
                except FileNotFoundError as error:
                    print(error)
                except OSError as error:
                    print(f"Kunne ikke starte lydavspilling: {error}")
                next_audio_time = now + random.uniform(3, 5)

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
        motor_speed_1 = 200
        motor_speed_2 = 200

        #fortsette vending som har startet
        if now < turn_until:
            motor_speed_1 = turn_speed_1
            motor_speed_2 = turn_speed_2

        elif dist_1 < obstacle_threshold_cm and dist_2 < 30.0 and dist_3 <30.0:
            #snu rundt 
            turn_until = now + turn_duration
            motor_speed_1 = 60
            motor_speed_2 = -60
            turn_speed_1 = motor_speed_1
            turn_speed_2 = motor_speed_2
        # hvis distansen på sensor 1 er mindre enn 15, sving til siden som har største avstand
        elif dist_1 < obstacle_threshold_cm:
            if dist_3 > dist_2 + side_margin:
                # Mest plass til høyre.
                motor_speed_1 = 120
                motor_speed_2 = -80
                turn_until = now + turn_duration_90
                turn_speed_1 = motor_speed_1
                turn_speed_2 = motor_speed_2
            else:
                # Mest plass til venstre.
                motor_speed_1 = -80
                motor_speed_2 = 120
                turn_until = now + turn_duration_90
                turn_speed_1 = motor_speed_1
                turn_speed_2 = motor_speed_2

        # Hindring på venstre side: sving høyre.
        elif dist_2 < obstacle_threshold_cm:
            motor_speed_1 = 120
            motor_speed_2 = -80
            turn_until = now + turn_duration_90
            turn_speed_1 = motor_speed_1
            turn_speed_2 = motor_speed_2

        # Hindring på høyre side: sving venstre.
        elif dist_3 < obstacle_threshold_cm:
            motor_speed_1 = -80
            motor_speed_2 = 120
            turn_until = now + turn_duration_90
            turn_speed_1 = motor_speed_1
            turn_speed_2 = motor_speed_2
        
        
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
