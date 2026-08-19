import pygame
import math
import sys
import asyncio

# --- Constants & Configuration ---
BG_COLOR = (30, 30, 30)          
LINE_COLOR = (236, 230, 226)     
SPRING_COLOR = (224, 122, 95)    
BLOCK_COLOR = (61, 90, 128)      
GRAPH_COLOR = (135, 194, 165)    
DIM_LINE = (100, 100, 100)       

# Physics Constants
MASS = 1.0
K = 39.478  # Picked so frequency is exactly 1 Hz (omega = 2*pi, f = 1)
C_FRICTION = 1.5

class UI_Button:
    def __init__(self, rect, text, action=None, is_square=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.is_square = is_square
        self.hovered = False

    def draw(self, surface, font):
        color = (80, 80, 80) if self.hovered else (50, 50, 50)
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, LINE_COLOR, self.rect, 2, border_radius=8)
        
        words = self.text.split(" ")
        if len(words) > 1 and self.is_square:
            t1 = font.render(words[0], True, LINE_COLOR)
            t2 = font.render(" ".join(words[1:]), True, LINE_COLOR)
            surface.blit(t1, t1.get_rect(center=(self.rect.centerx, self.rect.centery - 12)))
            surface.blit(t2, t2.get_rect(center=(self.rect.centerx, self.rect.centery + 12)))
        else:
            txt_surf = font.render(self.text, True, LINE_COLOR)
            surface.blit(txt_surf, txt_surf.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.action:
                self.action()

class UI_Switch:
    def __init__(self, x, y, text, default=False):
        self.rect = pygame.Rect(x, y, 40, 20)
        self.text = text
        self.state = default
        self.hovered = False

    def draw(self, surface, font):
        color = (135, 194, 165) if self.state else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        
        circle_x = self.rect.right - 10 if self.state else self.rect.left + 10
        pygame.draw.circle(surface, LINE_COLOR, (circle_x, self.rect.centery), 8)
        
        txt_surf = font.render(self.text, True, LINE_COLOR)
        surface.blit(txt_surf, (self.rect.right + 10, self.rect.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state
                return True
        return False

class UI_TextInput:
    def __init__(self, x, y, w, h, label, initial_val="1.0"):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.text = initial_val
        self.active = False

    def draw(self, surface, font):
        color = (135, 194, 165) if self.active else (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=4)
        
        lbl_surf = font.render(self.label, True, LINE_COLOR)
        surface.blit(lbl_surf, (self.rect.x, self.rect.y - 18))
        
        cursor = "|" if self.active and pygame.time.get_ticks() % 1000 < 500 else ""
        txt_surf = font.render(self.text + cursor, True, LINE_COLOR)
        surface.blit(txt_surf, (self.rect.x + 5, self.rect.y + 4))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if event.unicode.isnumeric() or (event.unicode == "." and "." not in self.text):
                    if len(self.text) < 6:
                        self.text += event.unicode
        return False

class UI_RadioButton:
    def __init__(self, x, y, text, k_value):
        self.rect = pygame.Rect(x, y, 14, 14)
        self.text = text
        self.k_value = k_value

    def draw(self, surface, font, current_k):
        # Determine if this button represents the currently active K value
        is_selected = (abs(current_k - self.k_value) < 0.1)
        color = (135, 194, 165) if is_selected else (100, 100, 100)
        
        pygame.draw.rect(surface, color, self.rect, border_radius=7)
        if is_selected:
            pygame.draw.circle(surface, BG_COLOR, self.rect.center, 3)
        
        txt_surf = font.render(self.text, True, LINE_COLOR)
        surface.blit(txt_surf, (self.rect.right + 8, self.rect.y - 2))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

def draw_spring(surface, color, start, end, width=3):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    angle = math.atan2(dy, dx)
    
    nodes = 25
    points = [start]
    
    body_length = max(10, length - 40)
    for i in range(nodes):
        t = i / (nodes - 1)
        node_x = 20 + t * body_length
        node_y = 12 if i % 2 == 0 else -12
        if i == 0 or i == nodes - 1: node_y = 0
        
        rx = start[0] + node_x * math.cos(angle) - node_y * math.sin(angle)
        ry = start[1] + node_x * math.sin(angle) + node_y * math.cos(angle)
        points.append((rx, ry))
    points.append(end)
    pygame.draw.lines(surface, color, False, points, width)

def draw_arrow(surface, color, start, end, arrow_size=10, width=2):
    pygame.draw.line(surface, color, start, end, width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    
    p1 = (end[0] - arrow_size * math.cos(angle - math.pi/6),
          end[1] - arrow_size * math.sin(angle - math.pi/6))
    p2 = (end[0] - arrow_size * math.cos(angle + math.pi/6),
          end[1] - arrow_size * math.sin(angle + math.pi/6))
    pygame.draw.polygon(surface, color, [end, p1, p2])

def draw_double_arrow(surface, color, start, end, width=2):
    draw_arrow(surface, color, start, end, width=width)
    draw_arrow(surface, color, end, start, width=width)

class App:
    def __init__(self):
        pygame.init()
        self.width, self.height = 1200, 800
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Physics Engine: Harmonic Motion")
        
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_large = pygame.font.SysFont("consolas", 18, bold=True)
        
        self.font_math = pygame.font.SysFont("timesnewroman", 20, italic=True)
        self.font_sub = pygame.font.SysFont("timesnewroman", 14)

        self.clock = pygame.time.Clock()
        self.mode = "OSC" 
        self.setup_ui()
        self.reset_physics()

    def setup_ui(self):
        btn_y = self.height * 0.8 + (self.height * 0.2 - 100) / 2
        center_x = self.width / 2
        self.btn_osc = UI_Button((center_x - 120, btn_y, 100, 100), "Oscillation", lambda: self.set_mode("OSC"), True)
        self.btn_shm = UI_Button((center_x + 20, btn_y, 100, 100), "Simple Harmonic", lambda: self.set_mode("SHM"), True)
        
        old_fric = self.sw_friction.state if hasattr(self, 'sw_friction') else False
        old_amp = self.sw_amplitude.state if hasattr(self, 'sw_amplitude') else False
        old_grp = self.sw_graph.state if hasattr(self, 'sw_graph') else False
        
        old_freq_text = self.freq_input.text if hasattr(self, 'freq_input') else f"{math.sqrt(K / MASS) / (2 * math.pi):.2f}"
        old_k_text = self.k_input.text if hasattr(self, 'k_input') else f"{K:.1f}"
        
        self.sw_friction = UI_Switch(20, 20, "Friction", old_fric)
        self.sw_amplitude = UI_Switch(20, 50, "Show Amplitude Arrow", old_amp)
        self.sw_graph = UI_Switch(20, 80, "Show graph", old_grp)
        self.btn_force_sin = UI_Button((20, 110, 140, 30), "Force sin then play", self.force_sin)
        self.btn_stop = UI_Button((20, 150, 140, 30), "Stop", self.stop_sim)
        self.btn_reset = UI_Button((20, 190, 140, 30), "Reset", self.reset_physics)
        
        base_y = 100 if self.mode == "OSC" else 250
        self.freq_input = UI_TextInput(20, base_y, 120, 25, "Freq (Hz) [Enter]:", old_freq_text)
        self.k_input = UI_TextInput(20, base_y + 60, 120, 25, "Spring Const (K):", old_k_text)
        
        self.radios = [
            UI_RadioButton(20, base_y + 100, "Default (K=39.5)", 39.478),
            UI_RadioButton(20, base_y + 125, "Slinky (Soft)", 15.0),
            UI_RadioButton(20, base_y + 150, "Suspension (Stiff)", 150.0)
        ]
        
    def set_mode(self, mode):
        self.mode = mode
        # Snap inputs and radios to the correct spot depending on mode
        base_y = 100 if self.mode == "OSC" else 250
        self.freq_input.rect.y = base_y
        self.k_input.rect.y = base_y + 60
        for i, rb in enumerate(self.radios):
            rb.rect.y = base_y + 100 + (i * 25)
        self.reset_physics()

    def sync_inputs(self):
        """Updates text boxes to accurately reflect the current K variable"""
        current_freq = math.sqrt(K / MASS) / (2 * math.pi)
        self.freq_input.text = f"{current_freq:.2f}"
        self.k_input.text = f"{K:.1f}"

    def force_sin(self):
        self.pos = self.eq_pos
        omega = math.sqrt(K / MASS)
        self.vel = -(150 * omega) if self.mode == "SHM" else (150 * omega)
        
        self.stopped = False
        self.dragging = False
        self.history.clear()
        self.sim_time = 0
        self.max_amp_dist = 150 

    def stop_sim(self):
        self.stopped = True

    def reset_physics(self):
        self.eq_pos = 500 if self.mode == "OSC" else 400
        self.pos = self.eq_pos
        self.vel = 0
        self.dragging = False
        self.stopped = False
        self.max_amp_dist = 0
        self.sim_time = 0
        self.history = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.setup_ui()
                
            self.btn_osc.handle_event(event)
            self.btn_shm.handle_event(event)
            self.sw_friction.handle_event(event)
            self.sw_amplitude.handle_event(event)
            
            # Watch for Frequency input
            if self.freq_input.handle_event(event):
                try:
                    new_f = float(self.freq_input.text)
                    if new_f > 0:
                        global K
                        new_k = (new_f * 2 * math.pi)**2 * MASS
                        # Keep K within reasonable limits to stop physics engines from exploding
                        K = max(5.0, min(new_k, 300.0))
                except ValueError:
                    pass
                self.sync_inputs()
                self.reset_physics()
                
            # Watch for Spring Constant (K) input
            if self.k_input.handle_event(event):
                try:
                    new_k = float(self.k_input.text)
                    global K
                    K = max(5.0, min(new_k, 300.0))
                except ValueError:
                    pass
                self.sync_inputs()
                self.reset_physics()
                
            # Watch for Radio Button clicks
            for rb in self.radios:
                if rb.handle_event(event):
                    global K
                    K = rb.k_value
                    self.sync_inputs()
                    self.reset_physics()
            
            if self.mode == "SHM":
                self.sw_graph.handle_event(event)
                self.btn_force_sin.handle_event(event)
                self.btn_stop.handle_event(event)
                self.btn_reset.handle_event(event)

            top_h = self.height * 0.8
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event.pos[1] < top_h:
                    self.dragging = True
                    self.stopped = False
                    self.history.clear()
                    self.sim_time = 0
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.dragging = False
                    self.vel = 0 
                    self.max_amp_dist = abs(self.pos - self.eq_pos)
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    if self.mode == "OSC":
                        self.pos = max(280, min(event.pos[0], self.width - 30))
                    elif self.mode == "SHM":
                        self.pos = max(130, min(event.pos[1], top_h - 30))
                    self.max_amp_dist = abs(self.pos - self.eq_pos)

    def update_physics(self, dt):
        if not self.dragging and not self.stopped:
            spring_force = -K * (self.pos - self.eq_pos)
            friction_force = -C_FRICTION * self.vel if self.sw_friction.state else 0
            acc = (spring_force + friction_force) / MASS
            self.vel += acc * dt
            self.pos += self.vel * dt
            
            if abs(self.pos - self.eq_pos) > self.max_amp_dist:
                if self.vel * dt > 0 and self.pos > self.eq_pos:
                    self.max_amp_dist = abs(self.pos - self.eq_pos)
                elif self.vel * dt < 0 and self.pos < self.eq_pos:
                    self.max_amp_dist = abs(self.pos - self.eq_pos)
                    
            if self.sw_friction.state and abs(self.vel) < 5 and abs(spring_force) < 5:
                self.max_amp_dist *= 0.99
                
            self.sim_time += dt
            
        if self.mode == "SHM" and self.sw_graph.state and not self.dragging:
            if not self.stopped:
                self.history.append((self.sim_time, self.pos))
            self.history = [(t, p) for t, p in self.history if self.sim_time - t < 10]

    def draw_latex_force(self, surface, color, center_x, bottom_y):
        txt_F = self.font_math.render("F", True, color)
        txt_s = self.font_sub.render("s", True, color)
        
        f_rect = txt_F.get_rect()
        s_rect = txt_s.get_rect()
        
        total_width = f_rect.width + s_rect.width
        start_x = center_x - (total_width // 2)
        
        surface.blit(txt_F, (start_x, bottom_y - f_rect.height))
        surface.blit(txt_s, (start_x + f_rect.width, bottom_y - s_rect.height + 4))

    def draw_oscillation(self, top_rect):
        vertex = (250, top_rect.bottom - 150)
        
        pygame.draw.line(self.screen, LINE_COLOR, (vertex[0], 50), vertex, 2)
        pygame.draw.line(self.screen, LINE_COLOR, vertex, (self.width - 50, vertex[1]), 2)
        
        block_rect = pygame.Rect(self.pos - 25, vertex[1] - 50, 50, 50)
        draw_spring(self.screen, SPRING_COLOR, (vertex[0], vertex[1] - 25), (block_rect.left, vertex[1] - 25))
        pygame.draw.rect(self.screen, BLOCK_COLOR, block_rect, border_radius=4)
        
        eq_y = vertex[1]
        pygame.draw.line(self.screen, LINE_COLOR, (self.eq_pos, eq_y - 10), (self.eq_pos, eq_y + 10), 2)
        
        txt_0 = self.font.render("0", True, LINE_COLOR)
        self.screen.blit(txt_0, txt_0.get_rect(center=(self.eq_pos, eq_y + 20)))
        
        txt_plus = self.font.render("+", True, LINE_COLOR)
        txt_minus = self.font.render("-", True, LINE_COLOR)
        self.screen.blit(txt_plus, txt_plus.get_rect(center=(self.eq_pos - 60, eq_y + 20)))
        self.screen.blit(txt_minus, txt_minus.get_rect(center=(self.eq_pos + 60, eq_y + 20)))
        
        draw_arrow(self.screen, LINE_COLOR, (self.eq_pos - 15, eq_y + 20), (self.eq_pos - 45, eq_y + 20))
        draw_arrow(self.screen, LINE_COLOR, (self.eq_pos + 15, eq_y + 20), (self.eq_pos + 45, eq_y + 20))

        force = -K * (self.pos - self.eq_pos)
        if abs(force) > 5:
            f_len = min(abs(force) * 0.5, 150)
            f_dir = -1 if force < 0 else 1
            start_arr = (block_rect.centerx, block_rect.top - 20)
            end_arr = (block_rect.centerx + f_len * f_dir, block_rect.top - 20)
            draw_arrow(self.screen, SPRING_COLOR, start_arr, end_arr, width=3)
            self.draw_latex_force(self.screen, SPRING_COLOR, (start_arr[0] + end_arr[0]) // 2, start_arr[1] - 8)

        freq = math.sqrt(K / MASS) / (2 * math.pi)
        period = 1 / freq if freq > 0 else 0
        txt_f = self.font.render(f"Frequency: {freq:.2f} Hz", True, LINE_COLOR)
        txt_p = self.font.render(f"Period: {period:.2f} s", True, LINE_COLOR)
        self.screen.blit(txt_f, (vertex[0], vertex[1] + 40))
        self.screen.blit(txt_p, (vertex[0], vertex[1] + 60))

        blink_alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() * 0.005))
        amp_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        line_col = (*LINE_COLOR[:3], blink_alpha)
        
        if self.max_amp_dist > 5:
            max_x = self.eq_pos + (self.max_amp_dist if self.pos >= self.eq_pos else -self.max_amp_dist)
            pygame.draw.line(amp_surf, line_col, (max_x, vertex[1] - 80), (max_x, vertex[1] + 20), 1)
            
            amp_str = f"Amplitude: {int(self.max_amp_dist)} px"
            txt_amp = self.font.render(amp_str, True, line_col)
            
            if self.sw_amplitude.state:
                y_arr = vertex[1] - 70
                draw_double_arrow(amp_surf, line_col, (self.eq_pos, y_arr), (max_x, y_arr))
                txt_rect = txt_amp.get_rect(midbottom=((self.eq_pos + max_x) // 2, y_arr - 5))
                amp_surf.blit(txt_amp, txt_rect)
            else:
                txt_rect = txt_amp.get_rect(bottomleft=(max_x + 5, vertex[1] - 60))
                amp_surf.blit(txt_amp, txt_rect)
                
        self.screen.blit(amp_surf, (0, 0))

    def draw_shm(self, top_rect):
        vertex = (250, 100) 
        
        pygame.draw.line(self.screen, LINE_COLOR, (vertex[0] - 50, vertex[1]), (vertex[0] + 50, vertex[1]), 2)
        pygame.draw.line(self.screen, LINE_COLOR, vertex, (vertex[0], top_rect.bottom - 50), 2)
        
        block_rect = pygame.Rect(vertex[0] - 25, self.pos - 25, 50, 50)
        draw_spring(self.screen, SPRING_COLOR, vertex, (vertex[0], block_rect.top))
        pygame.draw.rect(self.screen, BLOCK_COLOR, block_rect, border_radius=4)
        
        eq_x = vertex[0]
        pygame.draw.line(self.screen, LINE_COLOR, (eq_x - 10, self.eq_pos), (eq_x + 10, self.eq_pos), 2)
        txt_0 = self.font.render("0", True, LINE_COLOR)
        self.screen.blit(txt_0, txt_0.get_rect(center=(eq_x - 30, self.eq_pos)))
        
        force = -K * (self.pos - self.eq_pos)
        if abs(force) > 5:
            f_len = min(abs(force) * 0.5, 150)
            f_dir = -1 if force < 0 else 1
            start_arr = (block_rect.right + 20, block_rect.centery)
            end_arr = (block_rect.right + 20, block_rect.centery + f_len * f_dir)
            draw_arrow(self.screen, SPRING_COLOR, start_arr, end_arr, width=3)
            
            txt_y_pos = (start_arr[1] + end_arr[1]) // 2 + 10
            self.draw_latex_force(self.screen, SPRING_COLOR, start_arr[0] + 25, txt_y_pos)

        freq = math.sqrt(K / MASS) / (2 * math.pi)
        period = 1 / freq if freq > 0 else 0
        txt_f = self.font.render(f"Frequency: {freq:.2f} Hz", True, LINE_COLOR)
        txt_p = self.font.render(f"Period: {period:.2f} s", True, LINE_COLOR)
        self.screen.blit(txt_f, (vertex[0] - 130, vertex[1] + 20))
        self.screen.blit(txt_p, (vertex[0] - 130, vertex[1] + 40))

        if self.sw_graph.state:
            graph_origin_x = 450
            graph_end_x = self.width - 50
            
            pygame.draw.line(self.screen, LINE_COLOR, (graph_origin_x, self.eq_pos), (graph_end_x, self.eq_pos), 1) 
            pygame.draw.line(self.screen, LINE_COLOR, (graph_origin_x, 100), (graph_origin_x, top_rect.bottom - 50), 1) 
            
            lbl_time = self.font.render("+x (Time)", True, LINE_COLOR)
            self.screen.blit(lbl_time, (graph_end_x - 80, self.eq_pos + 10))
            
            lbl_yp = self.font.render("+y", True, LINE_COLOR)
            self.screen.blit(lbl_yp, (graph_origin_x - 25, 100))
            
            lbl_ym = self.font.render("-y", True, LINE_COLOR)
            self.screen.blit(lbl_ym, (graph_origin_x - 25, top_rect.bottom - 60))

            pts = []
            time_scale = 120 
            for t, y in self.history:
                px = graph_origin_x + (self.sim_time - t) * time_scale
                if px <= graph_end_x:
                    pts.append((px, y))
            
            if len(pts) > 1:
                pygame.draw.lines(self.screen, GRAPH_COLOR, False, pts, 2)
                
            pygame.draw.line(self.screen, DIM_LINE, (block_rect.right, self.pos), (graph_origin_x, self.pos), 1)

            blink_alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() * 0.005))
            mark_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            col_mark = (*LINE_COLOR[:3], blink_alpha)
            
            max_sec = int(self.sim_time)
            for s in range(max(0, max_sec - 10), max_sec + 1):
                mx = graph_origin_x + (self.sim_time - s) * time_scale
                if graph_origin_x <= mx <= graph_end_x:
                    pygame.draw.line(mark_surf, col_mark, (mx, self.eq_pos - 150), (mx, self.eq_pos + 150), 1)
                    txt_s = self.font.render(f"{s}s", True, col_mark)
                    mark_surf.blit(txt_s, (mx + 5, self.eq_pos - 145))
            
            self.screen.blit(mark_surf, (0, 0))

        blink_alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() * 0.005))
        amp_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        line_col = (*LINE_COLOR[:3], blink_alpha)
        
        if self.max_amp_dist > 5:
            max_y = self.eq_pos + (self.max_amp_dist if self.pos >= self.eq_pos else -self.max_amp_dist)
            pygame.draw.line(amp_surf, line_col, (vertex[0] - 80, max_y), (vertex[0] + 80, max_y), 1)
            
            amp_str = f"Amp: {int(self.max_amp_dist)} px"
            txt_amp = self.font.render(amp_str, True, line_col)
            
            if self.sw_amplitude.state:
                x_arr = vertex[0] - 70
                draw_double_arrow(amp_surf, line_col, (x_arr, self.eq_pos), (x_arr, max_y))
                txt_rect = txt_amp.get_rect(midright=(x_arr - 5, (self.eq_pos + max_y) // 2))
                amp_surf.blit(txt_amp, txt_rect)
            else:
                txt_rect = txt_amp.get_rect(bottomleft=(vertex[0] + 60, max_y - 5))
                amp_surf.blit(txt_amp, txt_rect)
                
        self.screen.blit(amp_surf, (0, 0))

    async def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            if dt > 0.1: dt = 0.1
            
            self.handle_events()
            self.update_physics(dt)
            
            self.screen.fill(BG_COLOR)
            
            top_h = self.height * 0.8
            top_rect = pygame.Rect(0, 0, self.width, top_h)
            pygame.draw.line(self.screen, DIM_LINE, (0, top_h), (self.width, top_h), 2)
            
            if self.mode == "OSC":
                self.draw_oscillation(top_rect)
            elif self.mode == "SHM":
                self.draw_shm(top_rect)
                
            self.btn_osc.draw(self.screen, self.font_large)
            self.btn_shm.draw(self.screen, self.font_large)
            
            self.sw_friction.draw(self.screen, self.font)
            self.sw_amplitude.draw(self.screen, self.font)
            self.freq_input.draw(self.screen, self.font)
            self.k_input.draw(self.screen, self.font)
            
            for rb in self.radios:
                rb.draw(self.screen, self.font, K)
            
            if self.mode == "SHM":
                self.sw_graph.draw(self.screen, self.font)
                self.btn_force_sin.draw(self.screen, self.font)
                self.btn_stop.draw(self.screen, self.font)
                self.btn_reset.draw(self.screen, self.font)
                
            # Draw Copyright in the top right corner
            copy_surf = self.font.render("(c) Sir Ed PHYS01G@LPUC 2025", True, (120, 120, 120))
            self.screen.blit(copy_surf, (self.width - copy_surf.get_width() - 15, 15))

            pygame.display.update()
            await asyncio.sleep(0) 

async def main():
    app = App()
    await app.run()

if __name__ == "__main__":
    asyncio.run(main())