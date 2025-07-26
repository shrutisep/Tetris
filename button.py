import pygame

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("No joystick detected!")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Joystick name:", joystick.get_name())
print("Number of buttons:", joystick.get_numbuttons())
print("Number of axes:", joystick.get_numaxes())
print("Number of hats:", joystick.get_numhats())

print("\nPress any button or move a stick on the controller...\n")

while True:
    pygame.event.pump()
    
    for i in range(joystick.get_numbuttons()):
        if joystick.get_button(i):
            print(f"Button {i} is pressed")

    for i in range(joystick.get_numaxes()):
        axis_val = joystick.get_axis(i)
        if abs(axis_val) > 0.2:
            print(f"Axis {i} moved: {axis_val:.2f}")

    for i in range(joystick.get_numhats()):
        hat_val = joystick.get_hat(i)
        if hat_val != (0, 0):
            print(f"Hat {i} moved: {hat_val}")
