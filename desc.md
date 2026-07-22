# Midnightmare — main.py 코드 설명

## 전체 구조

```
main.py
├── 초기화 (pygame, screen, clock, font)
├── class Player
│   ├── __init__
│   ├── update
│   ├── _facing_angle
│   ├── _in_sector  (static)
│   ├── do_attack
│   ├── do_dash
│   ├── take_damage
│   ├── _draw_sector  (static)
│   ├── draw_effects
│   └── draw
├── class Zombie
│   ├── __init__
│   ├── update
│   ├── take_damage
│   └── draw
├── spawn_zombie()
├── draw_centered()
├── draw_overlay()
├── draw_hud()
└── main()
```

---

## 초기화

```python
screen = pygame.display.set_mode((WIDTH, HEIGHT))   # 800×600 창 생성
clock  = pygame.time.Clock()                        # FPS 제어용
font / font_big / font_mid                          # HUD, 오버레이용 폰트 3종
```

`setting.py`에서 `*` import로 상수(WIDTH, HEIGHT, FPS, 색상 등)를 전부 가져온다.

---

## class Player

### `__init__`

| 속성 | 설명 |
|---|---|
| `images` | knight1~3.jpg를 PLAYER_SIZE(64)로 스케일한 Surface 리스트 |
| `frame`, `animation_speed` | 프레임 인덱스와 애니메이션 속도 (이동 중에만 증가) |
| `x`, `y` | 화면 중앙에서 시작하는 위치 |
| `hp` | 현재 HP (초기값 PLAYER_HP = 75) |
| `direction` | `"up"` / `"down"` / `"left"` / `"right"` |
| `attack_timer` | 공격 쿨다운 카운터 (0이면 사용 가능) |
| `dash_timer` | 돌진 쿨다운 카운터 |
| `attack_effect` | 공격 부채꼴 표시 지속 타이머 |
| `dash_effect` | 돌진 부채꼴 표시 지속 타이머 |
| `invincible` | 무적 프레임 카운터 (0이면 피격 가능) |
| `_dash_dx/dy/left` | 돌진 이동 방향 벡터와 남은 이동 거리 |

---

### `update()`

매 프레임 호출되며 다음을 처리한다.

1. **돌진 슬라이드**: `_dash_left > 0`이면 WASD 입력을 무시하고 `_dash_dx/dy` 방향으로 `PLAYER_SPEED × 3` 속도로 이동
2. **WASD 이동**: 돌진 중이 아닐 때 키 입력으로 위치와 `direction` 갱신
3. **화면 경계 클램프**
4. **애니메이션**: 이동 중이면 `frame` 증가, 정지 시 0으로 리셋
5. **타이머 감소**: `attack_timer`, `dash_timer`, `attack_effect`, `dash_effect`, `invincible` 모두 매 프레임 1씩 감소

---

### `_facing_angle()`

`direction` 문자열을 라디안 각도로 변환한다.

| direction | 각도 |
|---|---|
| right | 0 |
| down | π/2 |
| left | π |
| up | -π/2 |

`pygame`의 y축은 아래가 양수이므로 down이 π/2이다.

---

### `_in_sector()` (static)

**판정 핵심 함수.** 공격/돌진 히트박스를 계산한다.

```
_in_sector(cx, cy, tx, ty, radius, facing_rad, half_angle_rad, target_half_size=0)
```

- `(cx, cy)` — 플레이어 중심
- `(tx, ty)` — 좀비 중심
- `target_half_size` — 좀비 AABB 반크기 (ZOMBIE_SIZE // 2 = 32)

좀비의 **AABB에서 플레이어와 가장 가까운 점**을 구해 판정하기 때문에, 좀비 스프라이트 외곽이 부채꼴 테두리에 닿는 순간 히트한다. 중심점만 체크할 때 생기는 시각-판정 불일치를 해소한다.

```
near_x = clamp(cx, tx-half, tx+half)
near_y = clamp(cy, ty-half, ty+half)
→ dist, angle 계산 → 반경 & 각도 범위 체크
```

---

### `do_attack()` — O키

- 쿨다운: `ATTACK_COOLDOWN` (20프레임 ≈ 0.33초)
- 범위: 반경 `ATTACK_RANGE`(80px), 전방 **±90° (총 180°)** 부채꼴
- 데미지: `ATTACK_DAMAGE` (40)
- 범위 안의 모든 좀비에 동시 적용

---

### `do_dash()` — P키

- 쿨다운: `DASH_COOLDOWN` (90프레임 = 1.5초)
- 범위: 반경 `DASH_RANGE`(120px), 전방 **±45° (총 90°)** 부채꼴
- 데미지: `DASH_DAMAGE` (20) + 넉백 `DASH_KNOCKBACK`(50px)
- 이동: `_dash_left = DASH_DISTANCE`(120px) 세팅 → `update()`에서 고속 슬라이드
- **무적**: `invincible = FPS × 2 = 120프레임 (2초)` 발동

---

### `take_damage(dmg)`

```python
if self.invincible > 0:
    return          # 무적 중 데미지 무시
self.hp = max(0, self.hp - dmg)
```

---

### `_draw_sector()` (static)

`_in_sector`와 **완전히 동일한 파라미터**로 부채꼴을 그린다. 판정과 시각화가 같은 영역을 쓰도록 설계되어 있다.

- 호(arc)를 40개 점으로 근사한 폴리곤 생성
- `outline_only=False` → 채우기, `True` → 테두리만
- 화면 전체 크기의 SRCALPHA Surface에 그린 뒤 `screen.blit`

---

### `draw_effects()`

공격/돌진 직후 부채꼴 범위를 화면에 표시한다.

| 이펙트 | 색 | 각도 | 지속 |
|---|---|---|---|
| 공격 | `ATTACK_COLOR` (빨강) | ±90° | 12프레임 |
| 돌진 | `DASH_COLOR` (노랑) | ±45° | 20프레임 |

채우기(alpha 55)와 테두리(alpha 220) 두 겹으로 그려 가독성을 높인다. 시간이 지날수록 alpha가 줄어 자연스럽게 페이드아웃된다.

---

### `draw()`

1. `draw_effects()` 호출 (부채꼴 범위 표시)
2. 방향이 `"left"`면 이미지를 수평 flip
3. **무적 중**이면:
   - 4프레임 주기로 파란 색조 적용 (깜빡임)
   - 파란 타원 링을 플레이어 주변에 그림 (남은 시간에 비례해 투명해짐)
4. 스프라이트 blit
5. HP바 (빨강 배경 + 초록 잔여량, 스프라이트 위 12px)

---

## class Zombie

### `__init__`

- `images`: zombie1~3.jpg 3프레임 애니메이션
- `x`, `y`: 스폰 위치 (화면 가장자리)
- `hp`: `ZOMBIE_HP` (40)
- `alive`: `False`가 되면 리스트에서 제거됨
- `hit_flash`: 피격 시 붉은 깜빡임 타이머

### `update(player)`

매 프레임:
1. 플레이어 중심을 향해 `ZOMBIE_SPEED`(1.4px/frame)로 이동 (단순 추적 AI)
2. 애니메이션 프레임 증가
3. 플레이어와 거리 ≤ `ZOMBIE_ATTACK_RANGE`(40px)이면 `ZOMBIE_ATTACK_COOLDOWN`(60프레임) 주기로 `ZOMBIE_DAMAGE`(20) 데미지

### `take_damage(dmg)`

- HP 감소
- `hit_flash = 8` 세팅 (붉은 깜빡임 시작)
- HP ≤ 0이면 `alive = False`

### `draw()`

- `alive = False`면 즉시 리턴
- `hit_flash`가 홀수 프레임에만 붉은 색조 추가 (2프레임 깜빡임)
- HP바 (스프라이트 위 10px)

---

## 헬퍼 함수

### `spawn_zombie()`

4방향 가장자리 중 랜덤 선택 → 화면 밖에서 등장하는 Zombie 인스턴스 반환

| edge | 위치 |
|---|---|
| 0 | 위쪽 (y = -ZOMBIE_SIZE) |
| 1 | 아래쪽 (y = HEIGHT) |
| 2 | 왼쪽 (x = -ZOMBIE_SIZE) |
| 3 | 오른쪽 (x = WIDTH) |

### `draw_centered(text, font_obj, color, y_offset)`

텍스트를 화면 중앙에 blit. `y_offset`으로 수직 위치 조정.

### `draw_overlay(title, subtitle, title_color)`

게임 오버/승리 화면용. 검은 반투명(alpha 160) 오버레이 위에 타이틀과 서브타이틀을 표시.

---

## `draw_hud(player, spawned, killed)`

| 위치 | 내용 |
|---|---|
| 좌상단 | `Zombies: 처치수 / 20   Spawned: 스폰수` |
| 좌하단 | `[O] Attack  READY / cooldown` |
| 좌하단 | `[P] Dash    READY / cooldown` |
| 우하단 | `INVINCIBLE 1.8s` (무적 중일 때만, 파란색) |

---

## `main()` — 게임 루프

### 상태 머신

```
"playing"  →  hp <= 0         →  "gameover"
           →  killed >= 20    →  "win"
"gameover" / "win"  →  R키    →  main() 재귀 재시작
```

### 루프 순서 (매 프레임)

```
1. clock.tick(FPS)          ← 60fps 고정
2. 이벤트 처리              ← QUIT, O/P/R/ESC
3. 배경 fill + 격자 그리기
4. [playing 상태]
   ├── 스폰 타이머 감소 → SPAWN_DELAY(60프레임)마다 좀비 1마리 추가
   ├── player.update()
   ├── zombie.update(player) × N
   ├── 죽은 좀비 제거 & killed 카운트
   ├── 승리/게임오버 판정
   └── draw (좀비 → 플레이어 → HUD 순)
5. [gameover / win 상태]  ← 오버레이 표시
6. pygame.display.flip()
```

좀비 스폰은 `spawned < MAX_ZOMBIES(20)` 동안만 진행되며, 총 20마리를 모두 처치하고 화면에 남은 좀비가 없으면 승리한다.
