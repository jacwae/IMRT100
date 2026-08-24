# alt samlet i en kode
from pathlib import Path
import random
import subprocess
import sys
import time

import imrt_robot_serial


# Robotens styresløyfe kjører med 10 kommandoer per sekund.
EXECUTION_FREQUENCY = 10  # Hz
EXECUTION_PERIOD = 1.0 / EXECUTION_FREQUENCY

# Lydfilen må ligge i samme mappe som dette Python-programmet.
AUDIO_FILE = Path(__file__).with_name("dinosaur.wav")
MIN_AUDIO_WAIT = 3.0
MAX_AUDIO_WAIT = 5.0

OBSTACLE_THRESHOLD_CM = 18.0
TURN_DURATION = 1.34


def start_audio(file_path):
    """Start en WAV-fil uten å stanse robotens styresløyfe."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fant ikke lydfilen: {file_path}")

    print(f"Spiller: {file_path.name}")
    return subprocess.Popen(["aplay", "-q", str(file_path)])


def stop_audio(audio_process):
    """Stopp en lydprosess som fortsatt kjører."""
    if audio_process is None or audio_process.poll() is not None:
        return

    audio_process.terminate()
    try:
        audio_process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        audio_process.kill()
        audio_process.wait()


if not AUDIO_FILE.exists():
    print(f"Fant ikke lydfilen: {AUDIO_FILE}")
    sys.exit(1)


motor_serial = imrt_robot_serial.IMRTRobotSerial()

try:
    motor_serial.connect("/dev/ttyACM0")
except Exception as error:
    print("Could not open port. Is your robot connected?")
    print(f"Feilmelding: {error}")
    sys.exit(1)

motor_serial.run()

turn_until = 0.0
audio_process = None
next_audio_time = time.monotonic() + random.uniform(
    MIN_AUDIO_WAIT, MAX_AUDIO_WAIT
)

print("Entering loop. Ctrl+c to terminate")

try:
    while not motor_serial.shutdown_now:
        iteration_start_time = time.monotonic()
        now = time.monotonic()

        # Kontroller lydprosessen uten å vente på den.
        if audio_process is not None:
            return_code = audio_process.poll()
            if return_code is not None:
                if return_code != 0:
                    print(f"Lydavspillingen feilet (returkode {return_code}).")

                audio_process = None
                next_audio_time = now + random.uniform(
                    MIN_AUDIO_WAIT, MAX_AUDIO_WAIT
                )
        elif now >= next_audio_time:
            audio_process = start_audio(AUDIO_FILE)

        # Les avstandssensorene.
        dist_1 = motor_serial.get_dist_1()
        dist_2 = motor_serial.get_dist_2()
        dist_3 = motor_serial.get_dist_3()
        dist_4 = motor_serial.get_dist_4()
        print(
            "foran:", dist_1,
            "venstre:", dist_2,
            "høyre:", dist_3,
            "bak:", dist_4,
        )

        # Standardbevegelse: kjør fremover.
        speed_motor_1 = 160
        speed_motor_2 = 160

        # Fortsett en allerede påbegynt vending.
        if now < turn_until:
            speed_motor_1 = 60
            speed_motor_2 = -60

        # Hindring foran på alle de tre fremre sensorene: snu.
        elif (
            dist_1 < OBSTACLE_THRESHOLD_CM
            and dist_2 < 30.0
            and dist_3 < 30.0
        ):
            turn_until = now + TURN_DURATION
            speed_motor_1 = 60
            speed_motor_2 = -60

        # Hindring rett frem: sving mot siden med størst avstand.
        elif dist_1 < OBSTACLE_THRESHOLD_CM:
            if dist_2 > dist_3:
                speed_motor_1 = -80
                speed_motor_2 = 120
            else:
                speed_motor_1 = 120
                speed_motor_2 = -80

        # Hindring foran til venstre: sving mot høyre.
        elif (
            dist_2 < OBSTACLE_THRESHOLD_CM
            and dist_2 < dist_3
        ):
            speed_motor_1 = 120
            speed_motor_2 = -80

        # Hindring foran til høyre: sving mot venstre.
        elif dist_3 < OBSTACLE_THRESHOLD_CM:
            speed_motor_1 = -80
            speed_motor_2 = 120

        # Fri bane rett frem og like sideavstander: kjør roligere.
        elif (
            dist_1 > OBSTACLE_THRESHOLD_CM
            and dist_2 == dist_3
        ):
            speed_motor_1 = 60
            speed_motor_2 = 60

        # Begrens motorkommandoene til gyldig område.
        speed_motor_1 = max(-400, min(400, speed_motor_1))
        speed_motor_2 = max(-400, min(400, speed_motor_2))

        motor_serial.send_command(speed_motor_1, speed_motor_2)

        # Hold styresløyfen på omtrent 10 Hz.
        iteration_duration = time.monotonic() - iteration_start_time
        if iteration_duration < EXECUTION_PERIOD:
            time.sleep(EXECUTION_PERIOD - iteration_duration)

except KeyboardInterrupt:
    print("\nAvsluttet av brukeren")
except FileNotFoundError as error:
    # Gjelder både manglende WAV-fil og manglende aplay-program.
    print(f"Kunne ikke starte lydavspillingen: {error}")
except Exception as error:
    print(f"Programmet stoppet på grunn av en feil: {error}")
finally:
    # Sørg for at både motorene og lyden stopper ved avslutning.
    try:
        motor_serial.send_command(0, 0)
    except Exception:
        pass

    stop_audio(audio_process)
    print("Ha det!")