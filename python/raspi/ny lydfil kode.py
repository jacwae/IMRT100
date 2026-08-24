import pathlib as Path
import subprocess
# funk for faen
# Lydfilen ligger i samme mappe som Python-programmet
AUDIO_FILE = Path(__file__).with_name("dinosaur.wav")


def play_audio(file_path):
    """Spiller en WAV-fil gjennom Raspberry Pi-ens lydutgang."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fant ikke lydfilen: {file_path}")

    print(f"Spiller: {file_path.name}")
    subprocess.run(
        ["aplay", "-q", str(file_path)],
        check=True
    )


try:
    play_audio(AUDIO_FILE)

except KeyboardInterrupt:
    print("\nAvsluttet av brukeren")

except FileNotFoundError as error:
    print(error)

except subprocess.CalledProcessError:
    print("Lydfilen kunne ikke spilles.")

finally:
    print("Ha det!")