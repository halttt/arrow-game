import pygame
import sys
import math

# =====================常量定义=====================
SCREEN_W, SCREEN_H = 640, 720
FPS = 60
# 颜色
COLOR_BG        = (245, 245, 240)
COLOR_GRID      = (210, 210, 205)
COLOR_ARROW     = (60, 90, 160)
COLOR_ARROW_HL  = (90, 140, 220)
COLOR_TEXT      = (40, 40, 40)
COLOR_TEXT_DIM  = (120, 120, 120)
COLOR_BTN       = (70, 130, 180)
COLOR_BTN_HOVER = (100, 160, 210)
COLOR_BTN_TEXT  = (255, 255, 255)
COLOR_SHAKE     = (220, 70, 70)

CELL_SIZE = 80
GRID_ORIGIN_Y = 180
DIRS = {
    'U': (0, -1),
    'D': (0, 1),
    'L': (-1, 0),
    'R': (1, 0),
}

FONT_LARGE = None
FONT_MED  = None
FONT_SMALL = None
def init_fonts():
    global FONT_LARGE, FONT_MED, FONT_SMALL
    FONT_LARGE = pygame.font.Font(None, 56)
    FONT_MED   = pygame.font.Font(None, 28)
    FONT_SMALL = pygame.font.Font(None, 20)

# =====================关卡数据=====================
LEVELS = [
    {
        'cols': 4, 'rows': 4, 'misses': 3,
        'arrows': [
            (0,0,'D'), (1,0,'D'), (2,0,'D'), (3,0,'D'),
            (0,1,'D'), (1,1,'R'), (2,1,'R'), (3,1,'D'),
            (0,2,'D'), (1,2,'R'), (2,2,'R'), (3,2,'D'),
            (0,3,'R'), (1,3,'R'), (2,3,'R'), (3,3,'D'),
        ],
    },
    {
        'cols': 5, 'rows': 5, 'misses': 3,
        'arrows': [
            (0,0,'D'), (1,0,'D'), (2,0,'D'), (3,0,'D'), (4,0,'D'),
            (0,1,'D'), (1,1,'R'), (2,1,'R'), (3,1,'R'), (4,1,'D'),
            (0,2,'D'), (1,2,'R'), (2,2,'R'), (3,2,'R'), (4,2,'D'),
            (0,3,'D'), (1,3,'R'), (2,3,'R'), (3,3,'R'), (4,3,'D'),
            (0,4,'R'), (1,4,'R'), (2,4,'R'), (3,4,'R'), (4,4,'D'),
        ],
    },
    {
        'cols': 6, 'rows': 6, 'misses': 2,
        'arrows': [
            (0,0,'D'), (1,0,'D'), (2,0,'D'), (3,0,'D'), (4,0,'D'), (5,0,'D'),
            (0,1,'D'), (1,1,'R'), (2,1,'R'), (3,1,'R'), (4,1,'R'), (5,1,'D'),
            (0,2,'D'), (1,2,'R'), (2,2,'R'), (3,2,'R'), (4,2,'R'), (5,2,'D'),
            (0,3,'D'), (1,3,'R'), (2,3,'R'), (3,3,'R'), (4,3,'R'), (5,3,'D'),
            (0,4,'D'), (1,4,'R'), (2,4,'R'), (3,4,'R'), (4,4,'R'), (5,4,'D'),
            (0,5,'R'), (1,5,'R'), (2,5,'R'), (3,5,'R'), (4,5,'R'), (5,5,'D'),
        ],
    },
]

# =====================游戏状态 新增shake变量=====================
class GameState:
    def __init__(self):
        self.screen_mode = 'START'
        self.level_index = 0
        self.arrows = []
        self.remaining_misses = 3
        self.shake_arrow = None
        self.shake_timer = 0.0
        self.hover_arrow = None
        self.btn_restart = pygame.Rect(SCREEN_W // 2 - 90, SCREEN_H - 110, 180, 56)
    def load_level(self, idx):
        data = LEVELS[idx]
        self.level_index = idx
        self.arrows = [{'c': a[0], 'r': a[1], 'dir': a[2]} for a in data['arrows']]
        self.total_arrows = len(self.arrows)
        self.remaining_misses = data['misses']
        self.shake_arrow = None
        self.shake_timer = 0.0
        self.hover_arrow = None
        self.cols = data['cols']
        self.rows = data['rows']
    def arrow_at(self, c, r):
        for a in self.arrows:
            if a['c'] == c and a['r'] == r:
                return a
        return None

# =====================路径检测函数=====================
def has_blocker(state, arrow):
    dc, dr = DIRS[arrow['dir']]
    c, r = arrow['c'] + dc, arrow['r'] + dr
    while 0 <= c < state.cols and 0 <= r < state.rows:
        blocker = state.arrow_at(c, r)
        if blocker:
            return blocker
        c += dc
        r += dr
    return None

# =====================绘制函数，增加shake偏移参数=====================
def grid_to_pixel(state, c, r):
    ox = (SCREEN_W - CELL_SIZE * state.cols) // 2
    oy = GRID_ORIGIN_Y
    return ox + c * CELL_SIZE + CELL_SIZE // 2, oy + r * CELL_SIZE + CELL_SIZE // 2

def draw_arrow_shape(surface, cx, cy, direction, color, shake_offset):
    cx += shake_offset
    size = 25
    if direction == 'U':
        pygame.draw.line(surface, color, (cx, cy+size), (cx, cy-size), 4)
        pygame.draw.polygon(surface, color, [(cx, cy-size), (cx-12, cy-12), (cx+12, cy-12)])
    elif direction == 'D':
        pygame.draw.line(surface, color, (cx, cy-size), (cx, cy+size), 4)
        pygame.draw.polygon(surface, color, [(cx, cy+size), (cx-12, cy+12), (cx+12, cy+12)])
    elif direction == 'L':
        pygame.draw.line(surface, color, (cx+size, cy), (cx-size, cy), 4)
        pygame.draw.polygon(surface, color, [(cx-size, cy), (cx-12, cy-12), (cx-12, cy+12)])
    elif direction == 'R':
        pygame.draw.line(surface, color, (cx-size, cy), (cx+size, cy), 4)
        pygame.draw.polygon(surface, color, [(cx+size, cy), (cx+12, cy-12), (cx+12, cy+12)])

def draw_grid(surface, state):
    ox = (SCREEN_W - CELL_SIZE * state.cols) // 2
    oy = GRID_ORIGIN_Y
    for c in range(state.cols):
        for r in range(state.rows):
            rect = pygame.Rect(ox + c * CELL_SIZE, oy + r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(surface, COLOR_GRID, rect, 2)

def draw_arrows(surface, state):
    for a in state.arrows:
        cx, cy = grid_to_pixel(state, a['c'], a['r'])
        color = COLOR_ARROW
        if state.hover_arrow and state.hover_arrow['c'] == a['c'] and state.hover_arrow['r'] == a['r']:
            color = COLOR_ARROW_HL
        offset_x = 0
        if state.shake_arrow and state.shake_arrow['c'] == a['c'] and state.shake_arrow['r'] == a['r']:
            offset_x = int(math.sin(state.shake_timer * 40) * 8)
            color = COLOR_SHAKE
        draw_arrow_shape(surface, cx, cy, a['dir'], color, offset_x)

def draw_hud(surface, state):
    lv_text = FONT_MED.render(f"Level {state.level_index + 1}/{len(LEVELS)}", True, COLOR_TEXT)
    surface.blit(lv_text, (30, 30))
    arr_text = FONT_SMALL.render(f"Arrows: {len(state.arrows)} / {state.total_arrows}", True, COLOR_TEXT)
    surface.blit(arr_text, (SCREEN_W - 250, 38))
    miss_text = FONT_MED.render(f"Miss left: {state.remaining_misses}", True,
                                COLOR_SHAKE if state.remaining_misses <= 1 else COLOR_TEXT)
    surface.blit(miss_text, (30, 80))

def draw_button(surface, rect, text, mouse_pos):
    hover = rect.collidepoint(mouse_pos)
    color = COLOR_BTN_HOVER if hover else COLOR_BTN
    pygame.draw.rect(surface, color, rect, border_radius=10)
    txt = FONT_MED.render(text, True, COLOR_BTN_TEXT)
    surface.blit(txt, txt.get_rect(center=rect.center))

def draw_start_screen(surface, state, mouse_pos):
    surface.fill(COLOR_BG)
    title = FONT_LARGE.render("Arrow Game", True, COLOR_TEXT)
    surface.blit(title, title.get_rect(center=(SCREEN_W // 2, 200)))
    sub = FONT_SMALL.render("Click arrow: remove if no block, else miss", True, COLOR_TEXT_DIM)
    surface.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 280)))
    tip = FONT_SMALL.render("3 levels, 3 misses per level", True, COLOR_TEXT_DIM)
    surface.blit(tip, tip.get_rect(center=(SCREEN_W // 2, 320)))
    draw_button(surface, state.btn_restart, "Start Game", mouse_pos)

def draw_win_screen(surface, state, mouse_pos):
    surface.fill(COLOR_BG)
    title = FONT_LARGE.render("You Win!", True, (50, 150, 80))
    surface.blit(title, title.get_rect(center=(SCREEN_W // 2, 240)))
    sub = FONT_MED.render("Completed all levels", True, COLOR_TEXT)
    surface.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 320)))
    draw_button(surface, state.btn_restart, "Restart", mouse_pos)

def draw_lose_screen(surface, state, mouse_pos):
    surface.fill(COLOR_BG)
    title = FONT_LARGE.render("Game Over", True, COLOR_SHAKE)
    surface.blit(title, title.get_rect(center=(SCREEN_W // 2, 240)))
    sub = FONT_MED.render(f"Miss limit reached (Level {state.level_index + 1})", True, COLOR_TEXT)
    surface.blit(sub, sub.get_rect(center=(SCREEN_W // 2, 320)))
    draw_button(surface, state.btn_restart, "Restart", mouse_pos)

def draw_play_screen(surface, state, mouse_pos):
    surface.fill(COLOR_BG)
    draw_hud(surface, state)
    draw_grid(surface, state)
    draw_arrows(surface, state)

def screen_to_grid(state, mx, my):
    ox = (SCREEN_W - CELL_SIZE * state.cols) // 2
    oy = GRID_ORIGIN_Y
    if not (ox <= mx < ox + CELL_SIZE * state.cols):
        return None
    if not (oy <= my < oy + CELL_SIZE * state.rows):
        return None
    c = (mx - ox) // CELL_SIZE
    r = (my - oy) // CELL_SIZE
    return c, r

# =====================修改点击：阻挡扣失误、触发晃动、失败判断=====================
def handle_click(state, mx, my):
    if state.screen_mode in ('START', 'WIN', 'LOSE'):
        if state.btn_restart.collidepoint(mx, my):
            if state.screen_mode == 'START':
                state.load_level(0)
                state.screen_mode = 'PLAY'
            else:
                state.screen_mode = 'START'
            return True
        return False
    cell = screen_to_grid(state, mx, my)
    if cell is None:
        return False
    c, r = cell
    arrow = state.arrow_at(c, r)
    if arrow is None:
        return False
    blocker = has_blocker(state, arrow)
    if blocker is None:
        state.arrows.remove(arrow)
        if not state.arrows:
            if state.level_index + 1 < len(LEVELS):
                state.load_level(state.level_index + 1)
            else:
                state.screen_mode = 'WIN'
    else:
        state.remaining_misses -= 1
        state.shake_arrow = arrow
        state.shake_timer = 0.0
        if state.remaining_misses <= 0:
            state.screen_mode = 'LOSE'
    return True

# =====================主循环，更新晃动计时器=====================
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Arrow Game")
    clock = pygame.time.Clock()
    init_fonts()
    state = GameState()
    state.load_level(0)
    state.screen_mode = 'START'
    state.arrows = []
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_click(state, *event.pos)
        if state.shake_arrow and state.shake_timer < 0.5:
            state.shake_timer += dt
        else:
            state.shake_arrow = None
        state.hover_arrow = None
        if state.screen_mode == 'PLAY':
            cell = screen_to_grid(state, *mouse_pos)
            if cell:
                state.hover_arrow = state.arrow_at(*cell)
        if state.screen_mode == 'START':
            draw_start_screen(screen, state, mouse_pos)
        elif state.screen_mode == 'PLAY':
            draw_play_screen(screen, state, mouse_pos)
        elif state.screen_mode == 'WIN':
            draw_win_screen(screen, state, mouse_pos)
        elif state.screen_mode == 'LOSE':
            draw_lose_screen(screen, state, mouse_pos)
        pygame.display.flip()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
