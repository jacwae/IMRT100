import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("Ingen Xbox-kontroller funnet")
else:
    xbox = pygame.joystick.Joystick(0)
    xbox.init()
    print("Fant:", xbox.get_name())

    while True:
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print("Knapp:", event.button)

        time.sleep(0.01)