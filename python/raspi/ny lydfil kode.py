import os
import subprocess

LYDFIL = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "lydfil",
        "pwlpl-epic-t-rex-roaring-sound-effect-powerful-dinosaur-444199.mp3",
    )
)

if not os.path.isfile(LYDFIL):
    raise FileNotFoundError(f"Fant ikke lydfilen: {LYDFIL}")

prosess = None

try:
    prosess = subprocess.Popen(["mpg123", "-q", LYDFIL])
    prosess.wait()

except KeyboardInterrupt:
    print("Stoppet av bruker")

finally:
    if prosess is not None and prosess.poll() is None:
        prosess.terminate()

    print("Goodbye")