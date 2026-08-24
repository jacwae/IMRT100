
from pathlib import Path
import random
import subprocess
import sys
import time

import imrt_robot_serial



# Navigasjonslokken sender motorkommandoer med 10 Hz.
EXECUTION_FREQUENCY = 10  # Hz
EXECUTION_PERIOD = 1.0 / EXECUTION_FREQUENCY

# Lydfilen skal ligge i samme mappe som dette Python-programmet.
AUDIO_FILE = Path(__file__).with_name("dinosaur.wav")
MIN_AUDIO_WAIT = 3.0
MAX_AUDIO_WAIT = 5.0

OBSTACLE_THRESHOLD_CM = 15.0
TURN_DURATION = 1.34


def start_audio(file_path: Path):
    """Start WAV-avspilling uten a blokkere navigasjonslokken."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fant ikke lydfilen: {file_path}")

    print(f"Spiller: {file_path.name}")
    return subprocess.Popen(["aplay", "-q", str(file_path)])


def main():
    motor_serial = imrt_robot_serial.IMRTRobotSerial()

    try:
        motor_serial.connect("/dev/ttyACM0")
    except Exception as error:
        print("Could not open port. Is your robot connected?\nExiting program")
        print(f"Detaljer: {error}")
        sys.exit(1)

    motor_serial.run()

    # monotonic() pavirkes ikke dersom systemklokken blir endret.
    turn_until = 0.0
    next_audio_time = time.monotonic() + random.uniform(
        MIN_AUDIO_WAIT, MAX_AUDIO_WAIT
    )
    audio_process = None
    audio_enabled = True

    print("Entering loop. Ctrl+c to terminate")

    try:
        while not motor_serial.shutdown_now:
            iteration_start_time = time.monotonic()
            now = iteration_start_time

            # Kontroller om en tidligere lydavspilling er ferdig.
            if audio_process is not None and audio_process.poll() is not None:
                if audio_process.returncode != 0:
                    print("Lydfilen kunne ikke spilles.")
                audio_process = None
                next_audio_time = now + random.uniform(
                    MIN_AUDIO_WAIT, MAX_AUDIO_WAIT
                )

            # Start ny lyd nar ventetiden har gatt ut. Popen blokkerer ikke.
            if audio_enabled and audio_process is None and now >= next_audio_time:
                try:
                    audio_process = start_audio(AUDIO_FILE)
                except FileNotFoundError as error:
                    print(error)
                    audio_enabled = False
                except OSError as error:
                    print(f"Kunne ikke starte aplay: {error}")
                    audio_enabled = False

            dist_1 = motor_serial.get_dist_1()
            dist_2 = motor_serial.get_dist_2()
            dist_3 = motor_serial.get_dist_3()
            dist_4 = motor_serial.get_dist_4()
            print(
                "foran:", dist_1,
                " venstre:", dist_2,
                " hoyre:", dist_3,
                " bak:", dist_4,
            )

            # Standardbevegelse: kjor fremover.
            speed_motor_1 = 120
            speed_motor_2 = 120

            # Fortsett en allerede startet helomvending.
            if now < turn_until:
                speed_motor_1 = 60
                speed_motor_2 = -60

            # Hindring foran og tett pa begge sidesensorene: snu rundt.
            elif (
                dist_1 < OBSTACLE_THRESHOLD_CM
                and dist_2 < 30.0
                and dist_3 < 30.0
            ):
                turn_until = now + TURN_DURATION
                speed_motor_1 = 60
                speed_motor_2 = -60

            # Hindring rett foran: velg siden med storst avstand.
            elif dist_1 < OBSTACLE_THRESHOLD_CM:
                if dist_2 > dist_3:
                    speed_motor_1 = -80
                    speed_motor_2 = 120
                else:
                    speed_motor_1 = 120
                    speed_motor_2 = -80

            # Hindring foran til venstre: sving hoyre.
            elif dist_2 < OBSTACLE_THRESHOLD_CM and dist_2 < dist_3:
                speed_motor_1 = 120
                speed_motor_2 = -80

            # Hindring foran til hoyre: sving venstre.
            elif dist_3 < OBSTACLE_THRESHOLD_CM:
                speed_motor_1 = -80
                speed_motor_2 = 120

            # Beholder denne spesialregelen fra den opprinnelige koden.
            elif dist_1 > OBSTACLE_THRESHOLD_CM and dist_2 == dist_3:
                speed_motor_1 = 60
                speed_motor_2 = 60

            speed_motor_1 = max(-400, min(400, speed_motor_1))
            speed_motor_2 = max(-400, min(400, speed_motor_2))
            motor_serial.send_command(speed_motor_1, speed_motor_2)

            iteration_duration = time.monotonic() - iteration_start_time
            if iteration_duration < EXECUTION_PERIOD:
                time.sleep(EXECUTION_PERIOD - iteration_duration)

    except KeyboardInterrupt:
        print("\nAvsluttet av brukeren")

    finally:
        # Stopp motorene nar programmet avsluttes.
        try:
            motor_serial.send_command(0, 0)
        except Exception:
            pass

        # Stopp eventuell pagaende lydavspilling.
        if audio_process is not None and audio_process.poll() is None:
            audio_process.terminate()
            try:
                audio_process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                audio_process.kill()
                audio_process.wait()

        print("Goodbye")


if __name__ == "__main__":
    main()
