import os
import sys

# Biztosítjuk, hogy a csomag gyökérkönyvtáron kívülről és belülről indítva is megtalálható legyen
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame

from robot_controller.config import COLORS, DT, FIELD_HEIGHT, FIELD_WIDTH, FPS, HEIGHT, WIDTH
from robot_controller.controller import MotionController
from robot_controller.network import RobotClient
from robot_controller.robot import SimulatedRobot
from robot_controller.ui import ControlUI


def main():
    print("Available robots:", ", ".join(COLORS.keys()))
    selected_color = input("Which one to use? ").strip().lower()

    # A robot a pálya (FIELD_WIDTH x FIELD_HEIGHT) közepén indul
    robot = SimulatedRobot(FIELD_WIDTH // 2, FIELD_HEIGHT // 2, 0.0, color=selected_color)

    # Hálózati kliens példányosítása, bekötve a robot telemetria-feldolgozóját
    client = RobotClient(color=selected_color, on_telemetry=robot.on_telemetry_received)
    robot.color = client.color
    client.connect(exit_on_Failure=True)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Szimuláció streamelése: {client.color.upper()} robot")
    clock = pygame.time.Clock()

    motion = MotionController(initial_x=robot.x, initial_y=robot.y)
    ui = ControlUI()

    running = True
    while running:
        current_ticks = pygame.time.get_ticks()

        # 1. UI feliratok és kapcsolóállapotok frissítése
        ui.update_labels(motion, robot)

        # 2. Események kezelése
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                ui.handle_event(event, motion, robot, current_ticks)

        # 3. Sebességparancsok meghatározása az aktuális vezérlési mód alapján
        cmd_v, cmd_omega = motion.compute_step(
            robot.x, robot.y, robot.theta, current_ticks
        )

        # 4. Parancs formázása és streamelése 5 Hz-en (megállásnál / módváltásnál azonnal)
        cmd_str, sent_v, sent_omega = client.stream_velocity(
            motion.mode,
            cmd_v,
            cmd_omega,
            current_ticks,
            force=motion.consume_force_send(),
        )

        # 5. Robot pozíciójának frissítése:
        # - SZIMULÁLT módban a ténylegesen kiküldött (sent_v, sent_omega) 5 Hz-es paranccsal
        # - TELEMETRIA módban a robottól visszaérkezett valós elmozdulással
        robot.update(sent_v, sent_omega, DT)

        # 6. Képernyő kirajzolása
        ui.render(screen, robot, motion, cmd_str, client.color, current_ticks)
        pygame.display.flip()
        clock.tick(FPS)

    client.disconnect()
    pygame.quit()


if __name__ == "__main__":
    main()
