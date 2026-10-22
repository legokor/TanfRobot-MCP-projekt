import math
from collections import deque

from robot_controller.config import (
    DEFAULT_ACTION_DIST,
    DEFAULT_ACTION_TIME,
    DEFAULT_KP_OMEGA,
    DEFAULT_KP_V,
    DEFAULT_MAX_OMEGA,
    DEFAULT_MAX_V,
    MIN_EFFECTIVE_OMEGA_DEG_S,
    MIN_EFFECTIVE_V_MM_S,
    MM_PER_PIXEL,
    TARGET_STOP_TOLERANCE_MM,
    TWO_PHASE_ANGLE_ENTER_DEG,
    TWO_PHASE_ANGLE_EXIT_DEG,
)


class ServerController:
    """
    Zárt körös (P-szabályozó) pozícióvezérlő, amely a robot aktuális pozíciója
    és a célpont alapján számítja ki a (v, omega) sebességparancsokat.

    Támogat kétféle AUTO vezérlési stratégiát (two_phase_mode kapcsolóval):
    1. KÉTFÁZISÚ (two_phase_mode = True):
       - 1. fázis (FORDUL): Helyben ráfordul a célpontra (v = 0, omega != 0).
       - 2. fázis (MEGY): Ha már célra néz, egyenesen halad a célig (v > 0, omega = 0),
         kihasználva a robot STM32-es 100 Hz-es giroszkópos iránytartását.
    2. FOLYAMATOS (two_phase_mode = False):
       - Egyszerre ad ki v és omega parancsokat (íves pályán közelíti a célt).
    """

    def __init__(
        self,
        max_v: float = DEFAULT_MAX_V,
        max_omega: float = DEFAULT_MAX_OMEGA,
        kp_omega: float = DEFAULT_KP_OMEGA,
        kp_v: float = DEFAULT_KP_V,
        two_phase_mode: bool = True,
    ):
        self.max_v = max_v
        self.max_omega = max_omega
        self.Kp_omega = kp_omega
        self.Kp_v = kp_v

        self.two_phase_mode = two_phase_mode
        self.is_turning_phase = False

    def compute_commands(
        self,
        robot_x: float,
        robot_y: float,
        robot_theta: float,
        target_x: float,
        target_y: float,
    ) -> tuple[float, float]:
        dx = target_x - robot_x
        # Képernyő Y tengely megfordítása, hogy a felfelé irány legyen +Y (CCW pozitív szög)
        dy_world = robot_y - target_y

        distance_mm = math.hypot(dx, dy_world) * MM_PER_PIXEL

        if distance_mm < TARGET_STOP_TOLERANCE_MM:
            self.is_turning_phase = False
            return 0.0, 0.0

        target_angle = math.atan2(dy_world, dx)
        angle_diff = (target_angle - robot_theta + math.pi) % (2 * math.pi) - math.pi
        angle_diff_deg = math.degrees(angle_diff)

        # --- 1. KÉTFÁZISÚ VEZÉRLÉS (Fordul -> Egyenesen megy) ---
        if self.two_phase_mode:
            if abs(angle_diff_deg) > TWO_PHASE_ANGLE_ENTER_DEG:
                self.is_turning_phase = True
            elif abs(angle_diff_deg) <= TWO_PHASE_ANGLE_EXIT_DEG:
                self.is_turning_phase = False

            if self.is_turning_phase:
                omega = self.Kp_omega * angle_diff
                min_omega_rad = math.radians(MIN_EFFECTIVE_OMEGA_DEG_S)
                if abs(omega) < min_omega_rad:
                    omega = math.copysign(min_omega_rad, angle_diff)
                omega = max(min(omega, self.max_omega), -self.max_omega)
                return 0.0, omega
            else:
                v = self.Kp_v * distance_mm
                if v < MIN_EFFECTIVE_V_MM_S:
                    v = MIN_EFFECTIVE_V_MM_S
                v = max(min(v, self.max_v), -self.max_v)
                return v, 0.0

        # --- 2. FOLYAMATOS (ÍVES) VEZÉRLÉS ---
        self.is_turning_phase = False
        omega = self.Kp_omega * angle_diff
        directional_modifier = max(0.0, math.cos(angle_diff))
        v = self.Kp_v * distance_mm * directional_modifier

        v = max(min(v, self.max_v), -self.max_v)
        omega = max(min(omega, self.max_omega), -self.max_omega)

        return v, omega


class MotionController:
    """
    Magasabb szintű állapotgép és mozgásvezérlő egy robothoz.
    Kezeli az AUTO (célpontra menő), TIMED (időzített), MANUAL (kézi) és STOP módokat,
    valamint előkészíti a Command Queue (parancssor) alapú végrehajtást.
    """

    def __init__(self, initial_x: float, initial_y: float, server_controller: ServerController = None):
        self.server = server_controller or ServerController()

        # Állapotgépi változók
        self.mode = "AUTO"
        self.target_x = initial_x
        self.target_y = initial_y
        self.manual_v = 0.0
        self.manual_omega = 0.0
        self.force_next_send = False

        # Időzített mód változói
        self.action_time = DEFAULT_ACTION_TIME  # másodpercben
        self.action_dist = DEFAULT_ACTION_DIST  # cm-ben
        self.timed_end_ticks = 0

        # Előkészített parancssor (Command Queue) a későbbi összetett útvonalakhoz
        self.command_queue = deque()

    # --- Paraméterek módosítása ---

    def change_action_time(self, delta: float):
        self.action_time = max(0.5, self.action_time + delta)

    def change_action_dist(self, delta: float):
        self.action_dist = max(5.0, self.action_dist + delta)

    # --- Módváltó parancsok ---

    def start_timed_turn(self, angle_deg: float, current_ticks: int):
        """Időzített elfordulás indítása adott szöggel (fokban, + = balra, - = jobbra)."""
        self.mode = "TIMED"
        deg_per_sec = angle_deg / self.action_time
        self.manual_v = 0.0
        self.manual_omega = math.radians(deg_per_sec)
        self.timed_end_ticks = current_ticks + int(self.action_time * 1000)
        self.force_next_send = True

    def start_timed_distance(self, direction: float, current_ticks: int):
        """
        Időzített egyenes haladás a beállított action_dist (cm) távolságra.
        direction: +1.0 (előre) vagy -1.0 (hátra).
        """
        self.mode = "TIMED"
        speed_mm_s = (self.action_dist * 10.0) / self.action_time
        self.manual_v = direction * speed_mm_s
        self.manual_omega = 0.0
        self.timed_end_ticks = current_ticks + int(self.action_time * 1000)
        self.force_next_send = True

    def set_manual(self, v: float, omega: float):
        """Kézi sebességvezérlés beállítása (v: mm/s, omega: rad/s)."""
        self.mode = "MANUAL"
        self.manual_v = v
        self.manual_omega = omega
        self.force_next_send = True

    def set_stop(self):
        """Azonnali megállás (STOP mód)."""
        self.mode = "STOP"
        self.manual_v = 0.0
        self.manual_omega = 0.0
        self.command_queue.clear()
        self.force_next_send = True

    def set_auto_target(self, x: float, y: float):
        """Célpont kijelölése a térképen (AUTO mód)."""
        self.mode = "AUTO"
        self.target_x = x
        self.target_y = y
        self.server.is_turning_phase = True
        self.force_next_send = True

    def consume_force_send(self) -> bool:
        forced = self.force_next_send
        self.force_next_send = False
        return forced

    def get_remaining_timed_seconds(self, current_ticks: int) -> float:
        if self.mode != "TIMED":
            return 0.0
        return max(0.0, (self.timed_end_ticks - current_ticks) / 1000.0)

    # --- Fő ciklusbeli számítás ---

    def compute_step(
        self,
        robot_x: float,
        robot_y: float,
        robot_theta: float,
        current_ticks: int,
    ) -> tuple[float, float]:
        """
        Meghatározza az aktuális (cmd_v, cmd_omega) értékeket a jelenlegi mód alapján.
        """
        if self.mode == "AUTO":
            cmd_v, cmd_omega = self.server.compute_commands(
                robot_x, robot_y, robot_theta, self.target_x, self.target_y
            )
        elif self.mode == "TIMED":
            if current_ticks < self.timed_end_ticks:
                cmd_v, cmd_omega = self.manual_v, self.manual_omega
            else:
                self.mode = "MANUAL"
                self.manual_v, self.manual_omega = 0.0, 0.0
                cmd_v, cmd_omega = 0.0, 0.0
        elif self.mode == "STOP":
            cmd_v, cmd_omega = 0.0, 0.0
        else:
            cmd_v, cmd_omega = self.manual_v, self.manual_omega

        return cmd_v, cmd_omega
