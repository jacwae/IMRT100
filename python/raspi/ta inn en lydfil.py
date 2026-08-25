from pathlib import Path
import random
import subprocess
import time

# Lydfilen ligger i samme mappe som Python-programmet
AUDIO_FILE = Path(__file__).with_name("dinosaur.wav")


def play_audio(file_path):
    """Spiller en WAV-fil."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fant ikke lydfilen: {file_path}")

    print(f"Spiller: {file_path.name}")

    subprocess.run(
        ["aplay", "-q", str(file_path)],
        check=True
    )


try:
    while True:
        # Velg en tilfeldig ventetid mellom 3 og 5 sekunder
        wait_time = random.uniform(3, 5)

        print(f"Venter {wait_time:.1f} sekunder...")
        time.sleep(wait_time)

        play_audio(AUDIO_FILE)

except KeyboardInterrupt:
    print("\nAvsluttet av brukeren")

except FileNotFoundError as error:
    print(error)

except subprocess.CalledProcessError:
    print("Lydfilen kunne ikke spilles.")

finally:
    print("Ha det!")