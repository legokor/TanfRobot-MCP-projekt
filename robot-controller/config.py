import math

# --- Képernyő és pálya méretek ---
# A pálya (bal oldal): 900 x 800 pixel -> 180 cm x 160 cm (MM_PER_PIXEL = 2.0 mellett)
# A vezérlőpanel (jobb oldal): 320 x 800 pixel
FIELD_WIDTH = 900
FIELD_HEIGHT = 800
PANEL_WIDTH = 320

WIDTH = FIELD_WIDTH + PANEL_WIDTH
HEIGHT = FIELD_HEIGHT

FPS = 30
DT = 1.0 / FPS          # Delta time (időlépés másodpercben)
MM_PER_PIXEL = 2.0      # SKÁLA: 1 pixel = 2 mm (1 cm = 5 px, 5 cm = 25 px)

# Hálózati parancsküldési frekvencia (5 Hz = 200 ms)
COMMAND_SEND_HZ = 5.0
COMMAND_SEND_INTERVAL_MS = int(1000.0 / COMMAND_SEND_HZ)

# Négyzetrács beállítások
GRID_STEP_MM = 50.0     # 5 cm-es négyzetrács (50 mm = 25 px)
GRID_MAJOR_EVERY = 5    # Minden 5. vonal (25 cm) kiemelt

# --- Robot valós fizikai méretei (mm-ben) ---
ROBOT_WIDTH_MM = 160.0          # 16 cm széles
ROBOT_LENGTH_MM = 170.0         # 17 cm hosszú
WHEEL_AXLE_OFFSET_MM = 50.0     # Első kerekek tengelye a robot mértani közepétől 5 cm-re előre
WHEEL_DIAMETER_MM = 66.0        # ~6.6 cm kerékátmérő (api.c alapján)
WHEEL_WIDTH_MM = 18.0           # ~1.8 cm kerékszélesség
CASTER_OFFSET_MM = -60.0        # Hátsó görgő a mértani középtől 6 cm-re hátra (tengelytől 11 cm-re)
CASTER_RADIUS_MM = 12.0         # Hátsó görgő sugara

# --- A robot firmware (api.c) valós konstansai ---
ENCODER_COUNTS_PER_REV = 970.5
MM_PER_ENCODER_COUNT = 0.2136476

ROBOT_K_FF_V = 0.15506          # PWM / (mm/s) -> 70 PWM-nél ~451 mm/s
ROBOT_K_FF_W = 0.21635          # PWM / (fok/s) -> 70 PWM-nél ~323 fok/s
ROBOT_KP_V = 0.8                # P-szabályozó (PWM / mm hiba)
ROBOT_KP_W = 2.3                # P-szabályozó (PWM / fok hiba)
ROBOT_MAX_PWM = 70.0            # PWM szaturáció az api.c-ben (-70 .. +70)

# --- Szabályozó (ServerController) alapértelmezett paraméterek ---
DEFAULT_MAX_V = 120.0                       # Max haladási sebesség (mm/s)
DEFAULT_MAX_OMEGA = math.radians(90.0)      # Max szögsebesség (rad/s, 90 fok/s)
DEFAULT_KP_OMEGA = 1.8                      # Irányszög P-tag
DEFAULT_KP_V = 0.8                          # Távolság P-tag ((mm/s) / mm)
TARGET_STOP_TOLERANCE_MM = 10.0             # 1 cm-en belül megáll

# Kétfázisú (Fordul -> Megy) vezérlés hiszterézis szögei (fokban)
TWO_PHASE_ANGLE_ENTER_DEG = 8.0             # 8 fok felett megáll és helyben fordul
TWO_PHASE_ANGLE_EXIT_DEG = 3.0              # 3 fok alá érve elindul egyenesen
MIN_EFFECTIVE_V_MM_S = 20.0                 # Minimális haladási sebesség, hogy ne tapadjon le
MIN_EFFECTIVE_OMEGA_DEG_S = 15.0            # Minimális forgási sebesség

# --- Kézi és időzített vezérlés alapértelmezések ---
MANUAL_LINEAR_SPEED = 50.0          # mm/s (5 cm/s)
MANUAL_ANGULAR_SPEED_DEG = 45.0     # fok/s
DEFAULT_ACTION_TIME = 2.0           # s
DEFAULT_ACTION_DIST = 10.0          # cm

# --- Színek (RGB) ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 40, 40)
BLUE = (40, 100, 220)
GREEN = (30, 160, 60)
TEAL = (20, 140, 150)
ORANGE = (220, 120, 20)
GRAY = (100, 100, 100)
LIGHT_GRAY = (150, 150, 150)
DARK_GRAY = (60, 60, 60)
TRAIL_GRAY = (180, 180, 220)

# Pálya és UI színek
FIELD_BG = (248, 249, 252)
GRID_LINE_COLOR = (225, 228, 235)
GRID_MAJOR_COLOR = (190, 196, 210)
GRID_TEXT_COLOR = (130, 136, 150)
PANEL_BG = (235, 237, 242)
PANEL_BORDER = (180, 185, 195)
ROBOT_BODY_COLOR = (70, 130, 230)
ROBOT_BORDER_COLOR = (30, 60, 120)
WHEEL_COLOR = (40, 40, 45)
CASTER_COLOR = (120, 125, 135)

# --- Hálózati beállítások (server.js alapján definiált portok) ---
SERVER_HOST = "http://tanfrobot-pi.labor.legokor.hu"

COLORS = {
    'red': 14200,
    'green': 14201,
    'gray': 14202,
    'pink': 14203,
    'black': 14204,
}

DEFAULT_ROBOT_COLOR = 'gray'
