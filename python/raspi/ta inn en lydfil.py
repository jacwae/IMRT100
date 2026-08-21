import os
import time
import pygame

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

# pygame bruker Raspberry Pi sitt valgte lydkort, for eksempel AUX-utgangen.
pygame.mixer.init()

try:
    pygame.mixer.music.load(LYDFIL)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Terminated by user")

finally:
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    print("Goodbye")
