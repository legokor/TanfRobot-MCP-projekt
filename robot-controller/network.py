import math
import sys
import socketio

from robot_controller.config import (
    COLORS,
    COMMAND_SEND_INTERVAL_MS,
    DEFAULT_ROBOT_COLOR,
    SERVER_HOST,
)


class RobotClient:
    """
    Egyetlen fizikai robottal való Socket.IO kommunikációért felelős osztály.
    Kezeli a parancsok formázását, az 5 Hz-es (200 ms) küldési korlátozást,
    a duplikáció-szűrést, valamint a robottól érkező telemetria ('Data received') fogadását.
    """

    def __init__(self, color: str, host: str = SERVER_HOST, on_telemetry=None):
        color_clean = color.strip().lower()
        if color_clean not in COLORS:
            print(f"Unknown color '{color}'. Default setting: {DEFAULT_ROBOT_COLOR}")
            color_clean = DEFAULT_ROBOT_COLOR

        self.color = color_clean
        self.port = COLORS[self.color]
        self.server_url = f"{host}:{self.port}"

        self.sio = socketio.Client()
        self.last_cmd_str = "2 0 0"
        self.last_send_ticks = -COMMAND_SEND_INTERVAL_MS
        self.sent_v = 0.0
        self.sent_omega = 0.0

        self.latest_telemetry = None
        self.telemetry_count = 0
        self.on_telemetry = on_telemetry

        self._register_events()

    def _register_events(self):
        @self.sio.on('Data received')
        def on_data_received(data):
            self.latest_telemetry = data
            self.telemetry_count += 1
            if self.on_telemetry is not None:
                self.on_telemetry(data)

    def connect(self, exit_on_Failure: bool = True) -> bool:
        try:
            self.sio.connect(self.server_url)
            print(f"\n[+] Sikeresen csatlakozva a {self.color} robothoz a {self.port}-es porton!\n")
            return True
        except Exception as e:
            print(f"\n[-] Nem sikerült csatlakozni a socket szerverhez ({self.server_url}):", e)
            if exit_on_Failure:
                sys.exit(1)
            return False

    @staticmethod
    def format_velocity_command(mode: str, cmd_v: float, cmd_omega: float) -> tuple[str, float, float]:
        """
        A vezérlési mód és sebességértékek (v [mm/s], omega [rad/s]) alapján
        előállítja a robot által várt parancs stringet és a kerekített tényleges (v, omega) értékeket.
        """
        if mode == "STOP":
            return "0", 0.0, 0.0
        elif abs(cmd_v) < 0.1 and abs(cmd_omega) < 0.1:
            return "2 0 0", 0.0, 0.0
        else:
            cmd_omega_deg = math.degrees(cmd_omega)
            v_int = round(cmd_v)
            omega_int = round(cmd_omega_deg)
            return f"2 {v_int} {omega_int}", float(v_int), math.radians(float(omega_int))

    def stream_velocity(
        self,
        mode: str,
        cmd_v: float,
        cmd_omega: float,
        current_ticks: int,
        force: bool = False,
    ) -> tuple[str, float, float]:
        """
        Megformázza és legfeljebb 5 Hz-es (200 ms) sűrűséggel elküldi a sebességparancsot.
        Megállító parancs ("0" vagy "2 0 0") vagy force=True esetén azonnal küld!
        Visszaadja a roboton ténylegesen aktív (kiküldött) (cmd_str, sent_v, sent_omega) hármast.
        """
        cmd_str, quant_v, quant_omega = self.format_velocity_command(mode, cmd_v, cmd_omega)

        is_stop_cmd = cmd_str in ("0", "2 0 0")
        elapsed_ms = current_ticks - self.last_send_ticks

        should_send = False
        if cmd_str != self.last_cmd_str:
            if force or is_stop_cmd or elapsed_ms >= COMMAND_SEND_INTERVAL_MS:
                should_send = True

        if should_send:
            if self.sio.connected:
                self.sio.emit('sendMessage', cmd_str)
            self.last_cmd_str = cmd_str
            self.last_send_ticks = current_ticks
            self.sent_v = quant_v
            self.sent_omega = quant_omega
            print(f"Streamelt parancs ({mode}, 5Hz): {cmd_str}")

        return self.last_cmd_str, self.sent_v, self.sent_omega

    def disconnect(self):
        if self.sio.connected:
            self.sio.disconnect()
