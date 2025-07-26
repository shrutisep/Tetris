import pygame

pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Controller name:", joystick.get_name())
print("Buttons:", joystick.get_numbuttons())
print("Axes:", joystick.get_numaxes())

while True:
    pygame.event.pump()

    for i in range(joystick.get_numbuttons()):
        if joystick.get_button(i):
            print(f"Button {i} pressed")

    for i in range(joystick.get_numaxes()):
        val = joystick.get_axis(i)
        if abs(val) > 0.1:
            print(f"Axis {i}: {val}")
