import math
import random
import threading

from robot_controller.config import (
    MM_PER_PIXEL,
    ROBOT_K_FF_V,
    ROBOT_K_FF_W,
    ROBOT_MAX_PWM,
    WHEEL_AXLE_OFFSET_MM,
)


class SimulatedRobot:
    """
    A robot digitális ikre / állapotmodellje.
    Képes kétféle módon frissíteni a pozícióját (use_telemetry_odometry kapcsolóval):
    1. SZIMULÁLT (use_telemetry_odometry = False):
       A kiküldött (v, omega) parancsok alapján számolja a mozgást.
    2. TELEMETRIA (use_telemetry_odometry = True):
       A robottól visszaérkező 'Data received' csomagokban lévő, utolsó kiolvasás
       óta megtett valós elmozdulások (cpsa=delta_right_mm, cpsb=delta_left_mm,
       imu.gyro.z=delta_yaw_deg) alapján lépteti a robotot.
    """

    def __init__(
        self,
        x: float,
        y: float,
        theta: float = 0.0,
        color: str = "gray",
        enable_noise: bool = False,
    ):
        self.x = x
        self.y = y
        self.theta = theta
        self.color = color
        self.enable_noise = enable_noise

        # Kapcsolható: False = Szimulált mozgás, True = Telemetria alapú valós elmozdulás
        self.use_telemetry_odometry = False

        self.history = []
        self.max_history_len = 250

        # Telemetria állapot és szálbiztos puffer a beérkező elmozdulásokhoz
        self._tel_lock = threading.Lock()
        self._pending_delta_mm = 0.0
        self._pending_delta_deg = 0.0

        self.last_delta_left_mm = 0.0
        self.last_delta_right_mm = 0.0
        self.last_delta_yaw_deg = 0.0
        self.last_pwm_left = 0
        self.last_pwm_right = 0
        self.telemetry_packets = 0

    def on_telemetry_received(self, data: dict):
        """
        Socket.IO háttérszálból hívódik meg, amikor 'Data received' esemény érkezik.
        Kiolvassa az utolsó olvasás óta megtett elmozdulást (mm és fok).
        """
        if not isinstance(data, dict):
            return

        # A módosított tel.c-ben:
        # cpsa = delta_right_mm, cpsb = delta_left_mm, imu.gyro.z = delta_yaw_deg
        d_right_mm = float(data.get("cpsa", 0.0))
        d_left_mm = float(data.get("cpsb", 0.0))
        d_center_mm = 0.5 * (d_left_mm + d_right_mm)

        imu = data.get("imu", {})
        gyro = imu.get("gyro", {}) if isinstance(imu, dict) else {}
        if isinstance(gyro, dict):
            d_yaw_deg = float(gyro.get("z", gyro.get("gyro_z", 0.0)))
        else:
            d_yaw_deg = 0.0

        with self._tel_lock:
            self._pending_delta_mm += d_center_mm
            self._pending_delta_deg += d_yaw_deg

            self.last_delta_left_mm = d_left_mm
            self.last_delta_right_mm = d_right_mm
            self.last_delta_yaw_deg = d_yaw_deg
            self.last_pwm_right = int(data.get("motora", 0))
            self.last_pwm_left = int(data.get("motorb", 0))
            self.telemetry_packets += 1

    @staticmethod
    def apply_firmware_limits(v_mm_s: float, omega_rad_s: float) -> tuple[float, float]:
        """
        Az api.c-ben található feedforward és +/-70 PWM mixer szaturáció figyelembevétele.
        """
        w_deg_s = math.degrees(omega_rad_s)
        linear_pwm = v_mm_s * ROBOT_K_FF_V
        angular_pwm = w_deg_s * ROBOT_K_FF_W

        left_pwm = max(-ROBOT_MAX_PWM, min(ROBOT_MAX_PWM, linear_pwm - angular_pwm))
        right_pwm = max(-ROBOT_MAX_PWM, min(ROBOT_MAX_PWM, linear_pwm + angular_pwm))

        eff_linear_pwm = 0.5 * (left_pwm + right_pwm)
        eff_angular_pwm = 0.5 * (right_pwm - left_pwm)

        v_eff = eff_linear_pwm / ROBOT_K_FF_V
        w_deg_eff = eff_angular_pwm / ROBOT_K_FF_W
        return v_eff, math.radians(w_deg_eff)

    def update(self, v: float, omega: float, dt: float):
        """
        Pozíció frissítése a kiválasztott mód (SZIMULÁLT vs. TELEMETRIA) alapján.
        """
        with self._tel_lock:
            d_mm = self._pending_delta_mm
            d_deg = self._pending_delta_deg
            self._pending_delta_mm = 0.0
            self._pending_delta_deg = 0.0

        if self.use_telemetry_odometry:
            # Telemetria mód: kizárólag a robottól kapott valós elmozdulással léptetjük
            if abs(d_mm) > 1e-4 or abs(d_deg) > 1e-4:
                d_theta = math.radians(d_deg)
                mid_theta = self.theta + 0.5 * d_theta
                self.theta = (self.theta + d_theta + math.pi) % (2 * math.pi) - math.pi

                d_pixel = d_mm / MM_PER_PIXEL
                self.x += d_pixel * math.cos(mid_theta)
                self.y -= d_pixel * math.sin(mid_theta)
                self._record_history()
            return

        # Szimulált mód: a kiküldött (v, omega) parancs alapján számolunk
        v_actual, omega_actual = self.apply_firmware_limits(v, omega)

        if self.enable_noise:
            v_actual *= random.uniform(0.98, 1.02)
            omega_actual *= random.uniform(0.97, 1.03)

        self.theta += omega_actual * dt
        self.theta = (self.theta + math.pi) % (2 * math.pi) - math.pi

        v_pixel = v_actual / MM_PER_PIXEL
        self.x += v_pixel * math.cos(self.theta) * dt
        self.y -= v_pixel * math.sin(self.theta) * dt

        self._record_history()

    def get_geometric_center(self) -> tuple[float, float]:
        """
        Visszaadja a robot 17x16 cm-es testének mértani középpontját pixelben
        (ami az első keréktengelytől 5 cm-rel hátrébb található).
        """
        offset_px = WHEEL_AXLE_OFFSET_MM / MM_PER_PIXEL
        cx = self.x - offset_px * math.cos(self.theta)
        cy = self.y + offset_px * math.sin(self.theta)
        return cx, cy

    def local_to_screen(self, local_forward_mm: float, local_left_mm: float) -> tuple[float, float]:
        """
        A robot saját koordináta-rendszerében (origó: keréktengely közepe,
        +forward: előre mm-ben, +left: balra mm-ben) megadott pontot
        átváltja képernyő-koordinátákra (pixel).
        """
        fwd_px = local_forward_mm / MM_PER_PIXEL
        left_px = local_left_mm / MM_PER_PIXEL

        cos_t = math.cos(self.theta)
        sin_t = math.sin(self.theta)

        sx = self.x + fwd_px * cos_t - left_px * sin_t
        sy = self.y - fwd_px * sin_t - left_px * cos_t
        return sx, sy

    def set_pose(self, x: float, y: float, theta: float):
        """
        Pozíció és orientáció közvetlen beállítása.
        """
        with self._tel_lock:
            self._pending_delta_mm = 0.0
            self._pending_delta_deg = 0.0
        self.x = x
        self.y = y
        self.theta = (theta + math.pi) % (2 * math.pi) - math.pi
        self._record_history()

    def _record_history(self):
        if not self.history or math.hypot(self.x - self.history[-1][0], self.y - self.history[-1][1]) >= 1.0:
            self.history.append((self.x, self.y))
            if len(self.history) > self.max_history_len:
                self.history.pop(0)
