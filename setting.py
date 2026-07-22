# ==========================
# Midnightmare - setting.py
# ==========================

# 화면
WIDTH = 800
HEIGHT = 600
FPS = 60

# 플레이어
PLAYER_SIZE = 64
PLAYER_HP = 75
PLAYER_SPEED = 4

# 공격
ATTACK_DAMAGE = 40
ATTACK_RANGE = 80
ATTACK_COOLDOWN = 20     # 프레임

# 돌진
DASH_DAMAGE = 20
DASH_DISTANCE = 120
DASH_RANGE = 120
DASH_KNOCKBACK = 50
DASH_COOLDOWN = 90

# 좀비
ZOMBIE_SIZE = 64
ZOMBIE_HP = 40
ZOMBIE_DAMAGE = 20
ZOMBIE_SPEED = 1.4
ZOMBIE_ATTACK_RANGE = 40
ZOMBIE_ATTACK_COOLDOWN = 60

# 스폰
MAX_ZOMBIES = 20
SPAWN_DELAY = 60         # 1초마다 한 마리

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

RED = (220, 40, 40)
GREEN = (40, 220, 40)
BLUE = (50, 100, 255)

GRAY = (70, 70, 70)
DARK = (30, 30, 30)

# 공격 범위 색
ATTACK_COLOR = (255, 0, 0)

# 돌진 범위 색
DASH_COLOR = (255, 220, 0)

# 이미지
KNIGHT_IMAGES = [
    "assets/knight1.jpg",
    "assets/knight2.jpg",
    "assets/knight3.jpg"
]

ZOMBIE_IMAGES = [
    "assets/zombie1.jpg",
    "assets/zombie2.jpg",
    "assets/zombie3.jpg"
]
