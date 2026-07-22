# ==========================================
# Midnightmare
# main.py
# ==========================================

import pygame
import random

import math

from setting import *

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Midnightmare")

clock = pygame.time.Clock()

font      = pygame.font.SysFont("arial", 24)
font_big  = pygame.font.SysFont("arial", 52, bold=True)
font_mid  = pygame.font.SysFont("arial", 32)

# ==========================================
# Player
# ==========================================
class Player:

    def __init__(self):

        self.images = []
        for path in KNIGHT_IMAGES:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (PLAYER_SIZE, PLAYER_SIZE))
            self.images.append(img)

        self.frame           = 0
        self.animation_speed = 0.15
        self.image           = self.images[0]

        self.x = WIDTH  // 2
        self.y = HEIGHT // 2

        self.hp        = PLAYER_HP
        self.direction = "down"

        self.attack_timer  = 0
        self.dash_timer    = 0

        self.attack_effect = 0   # 공격 범위 표시 타이머
        self.dash_effect   = 0   # 돌진 범위 표시 타이머

        # 무적 타이머 (FPS 60 × 2초 = 120프레임)
        self.invincible    = 0

        # 돌진 이동 잔여 거리
        self._dash_dx    = 0
        self._dash_dy    = 0
        self._dash_left  = 0

    # ---------- update ----------
    def update(self):

        moving = False

        # 돌진 중이면 이동 입력 무시하고 슬라이드
        if self._dash_left > 0:
            step = min(self._dash_left, PLAYER_SPEED * 3)
            self.x += self._dash_dx * step
            self.y += self._dash_dy * step
            self._dash_left -= step
            moving = True
        else:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a]:
                self.x -= PLAYER_SPEED
                self.direction = "left"
                moving = True
            if keys[pygame.K_d]:
                self.x += PLAYER_SPEED
                self.direction = "right"
                moving = True
            if keys[pygame.K_w]:
                self.y -= PLAYER_SPEED
                self.direction = "up"
                moving = True
            if keys[pygame.K_s]:
                self.y += PLAYER_SPEED
                self.direction = "down"
                moving = True

        self.x = max(0, min(WIDTH  - PLAYER_SIZE, self.x))
        self.y = max(0, min(HEIGHT - PLAYER_SIZE, self.y))

        if moving:
            self.frame += self.animation_speed
            if self.frame >= len(self.images):
                self.frame = 0
        else:
            self.frame = 0

        self.image = self.images[int(self.frame)]

        if self.attack_timer > 0:
            self.attack_timer -= 1
        if self.dash_timer > 0:
            self.dash_timer -= 1
        if self.attack_effect > 0:
            self.attack_effect -= 1
        if self.dash_effect > 0:
            self.dash_effect -= 1
        if self.invincible > 0:
            self.invincible -= 1

    # ---------- 방향 → 각도(라디안) ----------
    def _facing_angle(self):
        return {
            "right": 0,
            "down":  math.pi / 2,
            "left":  math.pi,
            "up":    -math.pi / 2,
        }[self.direction]

    # ---------- 부채꼴 판정 헬퍼 ----------
    @staticmethod
    def _in_sector(cx, cy, tx, ty, radius, facing_rad, half_angle_rad,
                   target_half_size=0):
        """
        대상 AABB(중심 tx,ty / 반크기 target_half_size)의 가장 가까운 점이
        중심(cx,cy) 기준 반경 radius, facing_rad ± half_angle_rad 부채꼴 안에
        있으면 True.  target_half_size=0 이면 점 판정과 동일.
        """
        # AABB 에서 (cx,cy) 에 가장 가까운 점
        near_x = max(tx - target_half_size, min(cx, tx + target_half_size))
        near_y = max(ty - target_half_size, min(cy, ty + target_half_size))

        dist = math.hypot(near_x - cx, near_y - cy)
        if dist > radius:
            return False
        if dist == 0:
            return True
        angle = math.atan2(near_y - cy, near_x - cx)
        diff  = abs(math.atan2(math.sin(angle - facing_rad),
                               math.cos(angle - facing_rad)))
        return diff <= half_angle_rad

    # ---------- 공격 ----------
    def do_attack(self, zombies):
        """O키 공격 – 전방 180° 부채꼴(±90°) 범위 내 좀비에 ATTACK_DAMAGE"""
        if self.attack_timer > 0:
            return

        self.attack_timer  = ATTACK_COOLDOWN
        self.attack_effect = 12

        cx      = self.x + PLAYER_SIZE // 2
        cy      = self.y + PLAYER_SIZE // 2
        facing  = self._facing_angle()

        for z in zombies:
            zx = z.x + ZOMBIE_SIZE // 2
            zy = z.y + ZOMBIE_SIZE // 2
            if self._in_sector(cx, cy, zx, zy,
                               ATTACK_RANGE, facing, math.pi / 2,
                               ZOMBIE_SIZE // 2):
                z.take_damage(ATTACK_DAMAGE)

    # ---------- 돌진 ----------
    def do_dash(self, zombies):
        """P키 돌진 – 전방 90° 부채꼴(±45°) 범위 내 좀비에 DASH_DAMAGE + 넉백"""
        if self.dash_timer > 0:
            return

        self.dash_timer  = DASH_COOLDOWN
        self.dash_effect = 20
        self.invincible  = FPS * 2   # 2초 무적

        dir_map = {
            "up":    ( 0, -1),
            "down":  ( 0,  1),
            "left":  (-1,  0),
            "right": ( 1,  0),
        }
        dx, dy = dir_map[self.direction]

        self._dash_dx   = dx
        self._dash_dy   = dy
        self._dash_left = DASH_DISTANCE

        cx     = self.x + PLAYER_SIZE // 2
        cy     = self.y + PLAYER_SIZE // 2
        facing = self._facing_angle()

        for z in zombies:
            zx = z.x + ZOMBIE_SIZE // 2
            zy = z.y + ZOMBIE_SIZE // 2
            if self._in_sector(cx, cy, zx, zy,
                               DASH_RANGE, facing, math.pi / 4,
                               ZOMBIE_SIZE // 2):
                z.take_damage(DASH_DAMAGE)
                if math.hypot(zx - cx, zy - cy) > 0:
                    z.x += dx * DASH_KNOCKBACK
                    z.y += dy * DASH_KNOCKBACK
                z.x = max(0, min(WIDTH  - ZOMBIE_SIZE, z.x))
                z.y = max(0, min(HEIGHT - ZOMBIE_SIZE, z.y))

    # ---------- 피격 ----------
    def take_damage(self, dmg):
        if self.invincible > 0:
            return
        self.hp = max(0, self.hp - dmg)

    # ---------- 부채꼴 그리기 헬퍼 ----------
    @staticmethod
    def _draw_sector(cx, cy, radius, facing_rad, half_angle_rad, color_rgb, alpha, outline_only=False):
        """
        _in_sector 와 동일한 (cx,cy / radius / facing_rad / half_angle_rad) 파라미터.
        판정과 시각화가 완전히 같은 영역을 표현한다.
        """
        steps  = 40
        points = [(cx, cy)]

        start_angle = facing_rad - half_angle_rad
        end_angle   = facing_rad + half_angle_rad

        for i in range(steps + 1):
            a = start_angle + (end_angle - start_angle) * i / steps
            points.append((
                cx + math.cos(a) * radius,
                cy + math.sin(a) * radius,
            ))

        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        if outline_only:
            pygame.draw.polygon(surf, (*color_rgb, alpha), points, 2)
        else:
            pygame.draw.polygon(surf, (*color_rgb, alpha), points)
        screen.blit(surf, (0, 0))

    # ---------- 범위 표시 ----------
    def draw_effects(self):
        cx = self.x + PLAYER_SIZE // 2
        cy = self.y + PLAYER_SIZE // 2
        facing = self._facing_angle()

        if self.attack_effect > 0:
            # 채우기 (연하게)
            fill_alpha    = int(55  * self.attack_effect / 12)
            outline_alpha = int(220 * self.attack_effect / 12)
            self._draw_sector(cx, cy, ATTACK_RANGE, facing,
                              math.pi / 2,          # ±90° → 총 180°
                              ATTACK_COLOR, fill_alpha,    outline_only=False)
            self._draw_sector(cx, cy, ATTACK_RANGE, facing,
                              math.pi / 2,
                              ATTACK_COLOR, outline_alpha, outline_only=True)

        if self.dash_effect > 0:
            # 채우기 (연하게)
            fill_alpha    = int(55  * self.dash_effect / 20)
            outline_alpha = int(220 * self.dash_effect / 20)
            self._draw_sector(cx, cy, DASH_RANGE, facing,
                              math.pi / 4,          # ±45° → 총 90°
                              DASH_COLOR, fill_alpha,    outline_only=False)
            self._draw_sector(cx, cy, DASH_RANGE, facing,
                              math.pi / 4,
                              DASH_COLOR, outline_alpha, outline_only=True)

    # ---------- draw ----------
    def draw(self):
        self.draw_effects()

        img = self.image
        if self.direction == "left":
            img = pygame.transform.flip(img, True, False)

        # 무적 중 – 파란 광채 + 깜빡임
        if self.invincible > 0:
            # 깜빡임: 4프레임 주기로 토글
            if (self.invincible // 4) % 2 == 0:
                glow = img.copy()
                glow.fill((80, 180, 255, 120), special_flags=pygame.BLEND_RGBA_ADD)
                img = glow
            # 테두리 링
            cx = self.x + PLAYER_SIZE // 2
            cy = self.y + PLAYER_SIZE // 2
            ring_alpha = int(200 * self.invincible / (FPS * 2))
            ring_surf  = pygame.Surface((PLAYER_SIZE + 20, PLAYER_SIZE + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(ring_surf, (80, 180, 255, ring_alpha),
                                ring_surf.get_rect(), 3)
            screen.blit(ring_surf, (cx - (PLAYER_SIZE + 20) // 2,
                                    cy - (PLAYER_SIZE + 20) // 2))

        screen.blit(img, (self.x, self.y))

        # HP바
        pygame.draw.rect(screen, RED,   (self.x, self.y - 12, PLAYER_SIZE, 6))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 12,
                                          int(PLAYER_SIZE * max(0, self.hp / PLAYER_HP)), 6))


# ==========================================
# Zombie
# ==========================================
class Zombie:

    def __init__(self, x, y):

        self.images = []
        for path in ZOMBIE_IMAGES:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (ZOMBIE_SIZE, ZOMBIE_SIZE))
            self.images.append(img)

        self.frame           = 0
        self.animation_speed = 0.12
        self.image           = self.images[0]

        self.x = x
        self.y = y

        self.hp     = ZOMBIE_HP
        self.alive  = True

        self.attack_timer  = 0
        self.hit_flash     = 0   # 피격 시 붉은 깜빡임

    # ---------- update ----------
    def update(self, player):

        if not self.alive:
            return

        # 플레이어 방향으로 이동
        px = player.x + PLAYER_SIZE  // 2
        py = player.y + PLAYER_SIZE  // 2
        mx = self.x   + ZOMBIE_SIZE  // 2
        my = self.y   + ZOMBIE_SIZE  // 2

        dist = math.hypot(px - mx, py - my)

        if dist > 0:
            self.x += (px - mx) / dist * ZOMBIE_SPEED
            self.y += (py - my) / dist * ZOMBIE_SPEED

        self.x = max(0, min(WIDTH  - ZOMBIE_SIZE, self.x))
        self.y = max(0, min(HEIGHT - ZOMBIE_SIZE, self.y))

        # 애니메이션
        self.frame += self.animation_speed
        if self.frame >= len(self.images):
            self.frame = 0
        self.image = self.images[int(self.frame)]

        # 플레이어 공격
        if dist <= ZOMBIE_ATTACK_RANGE:
            if self.attack_timer <= 0:
                player.take_damage(ZOMBIE_DAMAGE)
                self.attack_timer = ZOMBIE_ATTACK_COOLDOWN

        if self.attack_timer > 0:
            self.attack_timer -= 1

        if self.hit_flash > 0:
            self.hit_flash -= 1

    # ---------- 피격 ----------
    def take_damage(self, dmg):
        self.hp -= dmg
        self.hit_flash = 8
        if self.hp <= 0:
            self.alive = False

    # ---------- draw ----------
    def draw(self):
        if not self.alive:
            return

        img = self.image

        # 피격 깜빡임 – 붉은 색조
        if self.hit_flash > 0 and self.hit_flash % 2 == 0:
            tinted = img.copy()
            tinted.fill((200, 0, 0, 100), special_flags=pygame.BLEND_RGBA_ADD)
            img = tinted

        screen.blit(img, (self.x, self.y))

        # HP바
        pygame.draw.rect(screen, RED,   (self.x, self.y - 10, ZOMBIE_SIZE, 5))
        pygame.draw.rect(screen, GREEN, (self.x, self.y - 10,
                                          int(ZOMBIE_SIZE * max(0, self.hp / ZOMBIE_HP)), 5))


# ==========================================
# 스폰 헬퍼
# ==========================================
def spawn_zombie():
    """화면 가장자리 랜덤 위치에 좀비 생성"""
    edge = random.randint(0, 3)
    if edge == 0:   # 위
        x = random.randint(0, WIDTH  - ZOMBIE_SIZE)
        y = -ZOMBIE_SIZE
    elif edge == 1: # 아래
        x = random.randint(0, WIDTH  - ZOMBIE_SIZE)
        y = HEIGHT
    elif edge == 2: # 왼쪽
        x = -ZOMBIE_SIZE
        y = random.randint(0, HEIGHT - ZOMBIE_SIZE)
    else:           # 오른쪽
        x = WIDTH
        y = random.randint(0, HEIGHT - ZOMBIE_SIZE)
    return Zombie(x, y)


# ==========================================
# 오버레이 헬퍼
# ==========================================
def draw_centered(text, font_obj, color, y_offset=0):
    surf = font_obj.render(text, True, color)
    rx = WIDTH  // 2 - surf.get_width()  // 2
    ry = HEIGHT // 2 - surf.get_height() // 2 + y_offset
    screen.blit(surf, (rx, ry))


def draw_overlay(title, subtitle, title_color):
    """반투명 오버레이 + 타이틀/서브타이틀"""
    dark = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dark.fill((0, 0, 0, 160))
    screen.blit(dark, (0, 0))
    draw_centered(title,    font_big, title_color,  -40)
    draw_centered(subtitle, font_mid, WHITE,          40)


# ==========================================
# HUD
# ==========================================
def draw_hud(player, spawned, killed):
    # 스코어
    info = font.render(
        f"Zombies: {killed} / {MAX_ZOMBIES}   Spawned: {spawned}",
        True, WHITE
    )
    screen.blit(info, (10, 10))

    # 쿨다운 표시
    atk_cd  = max(0, player.attack_timer)
    dash_cd = max(0, player.dash_timer)

    atk_txt  = font.render(f"[O] Attack  {'cooldown' if atk_cd  else 'READY'}", True,
                            GRAY if atk_cd  else GREEN)
    dash_txt = font.render(f"[P] Dash    {'cooldown' if dash_cd else 'READY'}", True,
                            GRAY if dash_cd else DASH_COLOR)

    screen.blit(atk_txt,  (10, HEIGHT - 60))
    screen.blit(dash_txt, (10, HEIGHT - 35))

    # 무적 표시
    if player.invincible > 0:
        secs    = player.invincible / FPS
        inv_txt = font.render(f"INVINCIBLE  {secs:.1f}s", True, (80, 180, 255))
        screen.blit(inv_txt, (WIDTH - inv_txt.get_width() - 10, HEIGHT - 35))


# ==========================================
# 메인 게임 루프
# ==========================================
def main():

    player  = Player()
    zombies = []

    spawned     = 0      # 지금까지 스폰한 수
    killed      = 0      # 처치한 수
    spawn_timer = 0

    state = "playing"    # "playing" | "gameover" | "win"

    running = True
    while running:

        clock.tick(FPS)

        # ---- 이벤트 ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if state == "playing":
                    if event.key == pygame.K_o:
                        player.do_attack(zombies)
                    if event.key == pygame.K_p:
                        player.do_dash(zombies)

                # 게임 오버 / 승리 화면에서 R로 재시작
                elif event.key == pygame.K_r:
                    main()          # 재귀 재시작
                    return

                elif event.key == pygame.K_ESCAPE:
                    running = False

        # ---- 배경 ----
        screen.fill(DARK)

        # 격자 (분위기용)
        for gx in range(0, WIDTH,  64):
            pygame.draw.line(screen, GRAY, (gx, 0), (gx, HEIGHT), 1)
        for gy in range(0, HEIGHT, 64):
            pygame.draw.line(screen, GRAY, (0, gy), (WIDTH, gy), 1)

        if state == "playing":

            # ---- 스폰 ----
            if spawned < MAX_ZOMBIES:
                spawn_timer -= 1
                if spawn_timer <= 0:
                    zombies.append(spawn_zombie())
                    spawned += 1
                    spawn_timer = SPAWN_DELAY

            # ---- 업데이트 ----
            player.update()

            for z in zombies:
                z.update(player)

            # 죽은 좀비 제거 & 카운트
            before = len(zombies)
            zombies = [z for z in zombies if z.alive]
            killed += before - len(zombies)

            # ---- 승리 / 게임 오버 판정 ----
            if player.hp <= 0:
                state = "gameover"

            elif killed >= MAX_ZOMBIES and len(zombies) == 0:
                state = "win"

            # ---- 그리기 ----
            for z in zombies:
                z.draw()

            player.draw()
            draw_hud(player, spawned, killed)

        elif state == "gameover":
            for z in zombies:
                z.draw()
            player.draw()
            draw_overlay("GAME OVER", "Press R to restart  |  ESC to quit", RED)

        elif state == "win":
            player.draw()
            draw_overlay("YOU WIN!", "Press R to restart  |  ESC to quit", (255, 230, 0))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
