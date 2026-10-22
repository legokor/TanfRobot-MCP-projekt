import math
import pygame

from robot_controller.config import (
    BLACK,
    BLUE,
    CASTER_COLOR,
    CASTER_OFFSET_MM,
    CASTER_RADIUS_MM,
    DARK_GRAY,
    FIELD_BG,
    FIELD_HEIGHT,
    FIELD_WIDTH,
    GRAY,
    GREEN,
    GRID_LINE_COLOR,
    GRID_MAJOR_COLOR,
    GRID_MAJOR_EVERY,
    GRID_STEP_MM,
    GRID_TEXT_COLOR,
    HEIGHT,
    LIGHT_GRAY,
    MANUAL_ANGULAR_SPEED_DEG,
    MANUAL_LINEAR_SPEED,
    MM_PER_PIXEL,
    ORANGE,
    PANEL_BG,
    PANEL_BORDER,
    PANEL_WIDTH,
    RED,
    ROBOT_BODY_COLOR,
    ROBOT_BORDER_COLOR,
    ROBOT_LENGTH_MM,
    ROBOT_WIDTH_MM,
    TEAL,
    TRAIL_GRAY,
    WHEEL_AXLE_OFFSET_MM,
    WHEEL_COLOR,
    WHEEL_DIAMETER_MM,
    WHEEL_WIDTH_MM,
    WHITE,
    WIDTH,
)
from robot_controller.controller import MotionController
from robot_controller.robot import SimulatedRobot


class Button:
    """Egyszerű UI Gomb osztály a Pygame-hez"""

    def __init__(self, x, y, w, h, text, color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)

        text_surf = font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False


def draw_grid(screen: pygame.Surface, small_font: pygame.font.Font):
    """
    5 cm-es (GRID_STEP_MM = 50 mm) négyzetrács kirajzolása a pályára,
    minden 5. vonalnál (25 cm) vastagabb vonallal és cm felirattal.
    """
    grid_rect = pygame.Rect(0, 0, FIELD_WIDTH, FIELD_HEIGHT)
    pygame.draw.rect(screen, FIELD_BG, grid_rect)

    step_px = int(round(GRID_STEP_MM / MM_PER_PIXEL))
    if step_px <= 0:
        return

    col_idx = 0
    for x in range(0, FIELD_WIDTH + 1, step_px):
        is_major = (col_idx % GRID_MAJOR_EVERY == 0)
        color = GRID_MAJOR_COLOR if is_major else GRID_LINE_COLOR
        width = 2 if is_major else 1
        pygame.draw.line(screen, color, (x, 0), (x, FIELD_HEIGHT), width)

        if is_major and col_idx > 0 and x < FIELD_WIDTH - 30:
            cm_val = int(round((x * MM_PER_PIXEL) / 10.0))
            lbl = small_font.render(f"{cm_val}cm", True, GRID_TEXT_COLOR)
            screen.blit(lbl, (x + 3, 4))
        col_idx += 1

    row_idx = 0
    for y in range(0, FIELD_HEIGHT + 1, step_px):
        is_major = (row_idx % GRID_MAJOR_EVERY == 0)
        color = GRID_MAJOR_COLOR if is_major else GRID_LINE_COLOR
        width = 2 if is_major else 1
        pygame.draw.line(screen, color, (0, y), (FIELD_WIDTH, y), width)

        if is_major and row_idx > 0 and y < FIELD_HEIGHT - 20:
            cm_val = int(round((y * MM_PER_PIXEL) / 10.0))
            lbl = small_font.render(f"{cm_val}cm", True, GRID_TEXT_COLOR)
            screen.blit(lbl, (4, y + 3))
        row_idx += 1


def _local_rect_polygon(
    robot: SimulatedRobot,
    fwd_min_mm: float,
    fwd_max_mm: float,
    left_min_mm: float,
    left_max_mm: float,
) -> list[tuple[float, float]]:
    corners_local = [
        (fwd_max_mm, left_max_mm),  # bal első
        (fwd_max_mm, left_min_mm),  # jobb első
        (fwd_min_mm, left_min_mm),  # jobb hátsó
        (fwd_min_mm, left_max_mm),  # bal hátsó
    ]
    return [robot.local_to_screen(f_mm, l_mm) for f_mm, l_mm in corners_local]


def draw_robot(screen: pygame.Surface, robot: SimulatedRobot):
    """
    A robot valós méretarányos kirajzolása:
    - Test: 17 cm hosszú (ROBOT_LENGTH_MM = 170), 16 cm széles (ROBOT_WIDTH_MM = 160)
    - Első keréktengely: a mértani középponttól 5 cm-rel (WHEEL_AXLE_OFFSET_MM = 50) előre
    - Két első meghajtott kerék a tengelyen + hátsó görgő (caster) hátul középen.
    """
    if len(robot.history) > 1:
        pygame.draw.lines(screen, TRAIL_GRAY, False, robot.history, 2)

    half_w = ROBOT_WIDTH_MM / 2.0       # 80 mm (8 cm)
    half_l = ROBOT_LENGTH_MM / 2.0      # 85 mm (8.5 cm)

    front_edge_mm = half_l - WHEEL_AXLE_OFFSET_MM
    rear_edge_mm = -half_l - WHEEL_AXLE_OFFSET_MM

    # 1. Robot alváz (17 cm x 16 cm téglalap)
    body_poly = _local_rect_polygon(robot, rear_edge_mm, front_edge_mm, -half_w, half_w)
    pygame.draw.polygon(screen, ROBOT_BODY_COLOR, body_poly)
    pygame.draw.polygon(screen, ROBOT_BORDER_COLOR, body_poly, 2)

    # 2. Hátsó görgő (caster wheel)
    caster_fwd_mm = -WHEEL_AXLE_OFFSET_MM + CASTER_OFFSET_MM
    caster_pos = robot.local_to_screen(caster_fwd_mm, 0.0)
    caster_radius_px = max(3, int(round(CASTER_RADIUS_MM / MM_PER_PIXEL)))
    pygame.draw.circle(screen, CASTER_COLOR, (int(caster_pos[0]), int(caster_pos[1])), caster_radius_px)
    pygame.draw.circle(screen, BLACK, (int(caster_pos[0]), int(caster_pos[1])), caster_radius_px, 1)
    caster_wheel_poly = _local_rect_polygon(
        robot,
        caster_fwd_mm - CASTER_RADIUS_MM * 0.8,
        caster_fwd_mm + CASTER_RADIUS_MM * 0.8,
        -4.0,
        4.0,
    )
    pygame.draw.polygon(screen, WHEEL_COLOR, caster_wheel_poly)

    # 3. Első keréktengely vonala
    axle_left = robot.local_to_screen(0.0, half_w - 2.0)
    axle_right = robot.local_to_screen(0.0, -half_w + 2.0)
    pygame.draw.line(screen, DARK_GRAY, axle_left, axle_right, 2)

    # 4. Két első meghajtott kerék
    wheel_half_len = WHEEL_DIAMETER_MM / 2.0
    left_wheel_poly = _local_rect_polygon(
        robot,
        -wheel_half_len,
        wheel_half_len,
        half_w - WHEEL_WIDTH_MM + 4.0,
        half_w + 4.0,
    )
    pygame.draw.polygon(screen, WHEEL_COLOR, left_wheel_poly)
    pygame.draw.polygon(screen, BLACK, left_wheel_poly, 1)

    right_wheel_poly = _local_rect_polygon(
        robot,
        -wheel_half_len,
        wheel_half_len,
        -half_w - 4.0,
        -half_w + WHEEL_WIDTH_MM - 4.0,
    )
    pygame.draw.polygon(screen, WHEEL_COLOR, right_wheel_poly)
    pygame.draw.polygon(screen, BLACK, right_wheel_poly, 1)

    # 5. Mértani középpont jelölése
    geom_cx, geom_cy = robot.get_geometric_center()
    pygame.draw.circle(screen, WHITE, (int(geom_cx), int(geom_cy)), 3)

    # 6. Tengelyközéppont (forgásközéppont) és piros irányvektor az orrig
    nose_pos = robot.local_to_screen(front_edge_mm, 0.0)
    pygame.draw.line(screen, RED, (int(robot.x), int(robot.y)), (int(nose_pos[0]), int(nose_pos[1])), 3)
    pygame.draw.circle(screen, RED, (int(robot.x), int(robot.y)), 4)


class ControlUI:
    """
    A Pygame grafikus felület (5 cm-es négyzetrácsos pálya, jobb oldali vezérlőpanel,
    módkapcsolók, gombok, eseménykezelés, HUD és valós méretarányú robot) kezelője.
    """

    def __init__(self):
        self.title_font = pygame.font.SysFont(None, 23)
        self.font = pygame.font.SysFont(None, 20)
        self.btn_font = pygame.font.SysFont(None, 19)
        self.small_font = pygame.font.SysFont(None, 16)

        self.panel_x = FIELD_WIDTH
        pad_x = self.panel_x + 25
        act_btn_w = 270
        self.act_x = pad_x

        # --- 1. MÓDKAPCSOLÓK (Szimuláció vs. Telemetria, Kétfázisú vs. Folyamatos) ---
        self.toggle_start_y = 190
        self.btn_toggle_odom = Button(
            pad_x, self.toggle_start_y, act_btn_w, 34, "Mozgás: SZIMULÁLT", TEAL, BLUE
        )
        self.btn_toggle_phase = Button(
            pad_x, self.toggle_start_y + 40, act_btn_w, 34, "AUTO: KÉTFÁZISÚ (Fordul->Megy)", GREEN, TEAL
        )

        # --- 2. Időzített (Action) gombok ---
        self.act_start_y = 285

        self.btn_time_down = Button(self.act_x + 170, self.act_start_y, 35, 28, "-", DARK_GRAY, GRAY)
        self.btn_time_up = Button(self.act_x + 215, self.act_start_y, 35, 28, "+", DARK_GRAY, GRAY)

        self.btn_dist_down = Button(self.act_x + 170, self.act_start_y + 34, 35, 28, "-", DARK_GRAY, GRAY)
        self.btn_dist_up = Button(self.act_x + 215, self.act_start_y + 34, 35, 28, "+", DARK_GRAY, GRAY)

        self.btn_r90 = Button(self.act_x, self.act_start_y + 72, act_btn_w, 34, "Jobbra 90 fok", GRAY, LIGHT_GRAY)
        self.btn_l45 = Button(self.act_x, self.act_start_y + 112, act_btn_w, 34, "Balra 45 fok", GRAY, LIGHT_GRAY)
        self.btn_fwd_dist = Button(self.act_x, self.act_start_y + 152, act_btn_w, 34, "Előre X cm", GRAY, LIGHT_GRAY)
        self.btn_back_dist = Button(self.act_x, self.act_start_y + 192, act_btn_w, 34, "Hátra X cm", GRAY, LIGHT_GRAY)

        # --- 3. Kézi vezérlés (D-Pad) gombjai ---
        btn_w, btn_h = 84, 38
        self.dpad_x = pad_x
        self.start_y = 555

        self.btn_fwd = Button(self.dpad_x + 93, self.start_y, btn_w, btn_h, "Előre", GRAY, LIGHT_GRAY)
        self.btn_left = Button(self.dpad_x, self.start_y + 44, btn_w, btn_h, "Balra", GRAY, LIGHT_GRAY)
        self.btn_stop = Button(self.dpad_x + 93, self.start_y + 44, btn_w, btn_h, "STOP", RED, (200, 0, 0))
        self.btn_right = Button(self.dpad_x + 186, self.start_y + 44, btn_w, btn_h, "Jobbra", GRAY, LIGHT_GRAY)
        self.btn_back = Button(self.dpad_x + 93, self.start_y + 88, btn_w, btn_h, "Hátra", GRAY, LIGHT_GRAY)

        # --- 4. Pozíció reset gomb ---
        self.btn_reset_pose = Button(
            pad_x, HEIGHT - 48, act_btn_w, 34, "Robot vissza középre", DARK_GRAY, GRAY
        )

        self.buttons = [
            self.btn_toggle_odom,
            self.btn_toggle_phase,
            self.btn_fwd,
            self.btn_left,
            self.btn_stop,
            self.btn_right,
            self.btn_back,
            self.btn_time_down,
            self.btn_time_up,
            self.btn_dist_down,
            self.btn_dist_up,
            self.btn_r90,
            self.btn_l45,
            self.btn_fwd_dist,
            self.btn_back_dist,
            self.btn_reset_pose,
        ]

    def update_labels(self, motion: MotionController, robot: SimulatedRobot):
        """Dinamikus gombfeliratok és színek frissítése."""
        self.btn_fwd_dist.text = f"Előre {int(motion.action_dist)} cm"
        self.btn_back_dist.text = f"Hátra {int(motion.action_dist)} cm"

        if robot.use_telemetry_odometry:
            self.btn_toggle_odom.text = "Mozgás: TELEMETRIA (Valós)"
            self.btn_toggle_odom.color = ORANGE
        else:
            self.btn_toggle_odom.text = "Mozgás: SZIMULÁLT (Parancs)"
            self.btn_toggle_odom.color = TEAL

        if motion.server.two_phase_mode:
            self.btn_toggle_phase.text = "AUTO: KÉTFÁZISÚ (Fordul->Megy)"
            self.btn_toggle_phase.color = GREEN
        else:
            self.btn_toggle_phase.text = "AUTO: FOLYAMATOS (Íves)"
            self.btn_toggle_phase.color = BLUE

    def handle_event(
        self,
        event: pygame.event.Event,
        motion: MotionController,
        robot: SimulatedRobot,
        current_ticks: int,
    ):
        """Egéresemények (hover, gombkattintás, térképkattintás) feldolgozása."""
        if event.type == pygame.MOUSEMOTION:
            for b in self.buttons:
                b.check_hover(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            clicked_on_button = False

            # --- MÓDKAPCSOLÓK ---
            if self.btn_toggle_odom.is_clicked(event):
                robot.use_telemetry_odometry = not robot.use_telemetry_odometry
                clicked_on_button = True
            elif self.btn_toggle_phase.is_clicked(event):
                motion.server.two_phase_mode = not motion.server.two_phase_mode
                motion.server.is_turning_phase = True
                motion.force_next_send = True
                clicked_on_button = True

            # --- IDŐ BEÁLLÍTÁSA ---
            elif self.btn_time_up.is_clicked(event):
                motion.change_action_time(0.5)
                clicked_on_button = True
            elif self.btn_time_down.is_clicked(event):
                motion.change_action_time(-0.5)
                clicked_on_button = True

            # --- TÁVOLSÁG BEÁLLÍTÁSA ---
            elif self.btn_dist_up.is_clicked(event):
                motion.change_action_dist(5.0)
                clicked_on_button = True
            elif self.btn_dist_down.is_clicked(event):
                motion.change_action_dist(-5.0)
                clicked_on_button = True

            # --- IDŐZÍTETT PARANCSOK (TIMED MÓD) ---
            elif self.btn_r90.is_clicked(event):
                motion.start_timed_turn(-90.0, current_ticks)
                clicked_on_button = True
            elif self.btn_l45.is_clicked(event):
                motion.start_timed_turn(45.0, current_ticks)
                clicked_on_button = True

            # --- TÁVOLSÁG ALAPÚ PARANCSOK (TIMED MÓD) ---
            elif self.btn_fwd_dist.is_clicked(event):
                motion.start_timed_distance(1.0, current_ticks)
                clicked_on_button = True
            elif self.btn_back_dist.is_clicked(event):
                motion.start_timed_distance(-1.0, current_ticks)
                clicked_on_button = True

            # --- KÉZI PARANCSOK (MANUAL MÓD) ---
            elif self.btn_fwd.is_clicked(event):
                motion.set_manual(MANUAL_LINEAR_SPEED, 0.0)
                clicked_on_button = True
            elif self.btn_back.is_clicked(event):
                motion.set_manual(-MANUAL_LINEAR_SPEED, 0.0)
                clicked_on_button = True
            elif self.btn_left.is_clicked(event):
                motion.set_manual(0.0, math.radians(MANUAL_ANGULAR_SPEED_DEG))
                clicked_on_button = True
            elif self.btn_right.is_clicked(event):
                motion.set_manual(0.0, math.radians(-MANUAL_ANGULAR_SPEED_DEG))
                clicked_on_button = True
            elif self.btn_stop.is_clicked(event):
                motion.set_stop()
                clicked_on_button = True
            elif self.btn_reset_pose.is_clicked(event):
                cx, cy = FIELD_WIDTH // 2, FIELD_HEIGHT // 2
                robot.history.clear()
                robot.set_pose(cx, cy, 0.0)
                motion.set_auto_target(cx, cy)
                motion.set_stop()
                clicked_on_button = True

            # --- PÁLYA KATTINTÁS (AUTO MÓD) ---
            if not clicked_on_button and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if mx < FIELD_WIDTH:
                    motion.set_auto_target(mx, my)

    def render(
        self,
        screen: pygame.Surface,
        robot: SimulatedRobot,
        motion: MotionController,
        cmd_str: str,
        selected_color: str,
        current_ticks: int,
    ):
        """A teljes képernyő (5 cm-es rácsos pálya, valós méretű robot, vezérlőpanel) kirajzolása."""
        draw_grid(screen, self.small_font)

        if motion.mode == "AUTO":
            tx, ty = int(motion.target_x), int(motion.target_y)
            pygame.draw.line(screen, (180, 230, 180), (int(robot.x), int(robot.y)), (tx, ty), 1)
            pygame.draw.circle(screen, GREEN, (tx, ty), 5)
            pygame.draw.circle(screen, GREEN, (tx, ty), 12, 2)

        draw_robot(screen, robot)

        panel_rect = pygame.Rect(self.panel_x, 0, PANEL_WIDTH, HEIGHT)
        pygame.draw.rect(screen, PANEL_BG, panel_rect)
        pygame.draw.line(screen, PANEL_BORDER, (self.panel_x, 0), (self.panel_x, HEIGHT), 2)

        # HUD információk
        x_cm = (robot.x * MM_PER_PIXEL) / 10.0
        y_cm = (robot.y * MM_PER_PIXEL) / 10.0
        deg = math.degrees(robot.theta)
        dist_to_target_cm = (
            math.hypot(motion.target_x - robot.x, motion.target_y - robot.y) * MM_PER_PIXEL / 10.0
        )

        mode_str = f"MÓD: {motion.mode}"
        if motion.mode == "TIMED":
            remaining = motion.get_remaining_timed_seconds(current_ticks)
            mode_str += f" ({remaining:.1f}s)"
        elif motion.mode == "AUTO" and motion.server.two_phase_mode:
            phase_txt = "FORDUL" if motion.server.is_turning_phase else "MEGY"
            mode_str += f" [{phase_txt}]"

        tel_str = (
            f"Tel(#{robot.telemetry_packets}): "
            f"dB={robot.last_delta_left_mm:.0f}mm "
            f"dJ={robot.last_delta_right_mm:.0f}mm "
            f"dSz={robot.last_delta_yaw_deg:.0f}°"
        )

        hud_lines = [
            (f"ROBOT: {selected_color.upper()} (5 Hz stream)", self.title_font, BLACK),
            (mode_str, self.font, BLUE if motion.mode == "AUTO" else BLACK),
            (f"Kiküldött: {cmd_str}", self.font, DARK_GRAY),
            (f"Poz: X={x_cm:.1f}cm, Y={y_cm:.1f}cm | {deg:.1f}°", self.font, DARK_GRAY),
            (f"Cél távolság: {dist_to_target_cm:.1f} cm", self.font, DARK_GRAY),
            (tel_str, self.small_font, ORANGE if robot.use_telemetry_odometry else GRID_TEXT_COLOR),
            (
                f"PWM B/J: {robot.last_pwm_left} / {robot.last_pwm_right}",
                self.small_font,
                GRID_TEXT_COLOR,
            ),
        ]

        hud_y = 12
        for text, fnt, col in hud_lines:
            surf = fnt.render(text, True, col)
            screen.blit(surf, (self.act_x, hud_y))
            hud_y += 24

        pygame.draw.line(
            screen, PANEL_BORDER, (self.panel_x + 15, 182), (WIDTH - 15, 182), 1
        )
        pygame.draw.line(
            screen, PANEL_BORDER, (self.panel_x + 15, 274), (WIDTH - 15, 274), 1
        )

        time_text = f"Időtartam: {motion.action_time:.1f} s"
        time_surf = self.font.render(time_text, True, BLACK)
        screen.blit(time_surf, (self.act_x, self.act_start_y + 6))

        dist_text = f"Távolság: {motion.action_dist:.0f} cm"
        dist_surf = self.font.render(dist_text, True, BLACK)
        screen.blit(dist_surf, (self.act_x, self.act_start_y + 40))

        pygame.draw.line(
            screen, PANEL_BORDER, (self.panel_x + 15, 520), (WIDTH - 15, 520), 1
        )
        manual_lbl = self.font.render("Kézi vezérlés (D-Pad):", True, BLACK)
        screen.blit(manual_lbl, (self.act_x, 530))

        for b in self.buttons:
            b.draw(screen, self.btn_font)
