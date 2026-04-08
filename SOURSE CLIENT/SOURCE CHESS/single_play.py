import pygame
import sys
import time
import random
import threading
import chess
import chess.engine
import audio_manager
import subprocess

class SinglePlayUI:
    def __init__(self, surface):
        self.surface = surface
        self.state = "LEVEL_SELECT" # "LEVEL_SELECT" hoặc "PLAYING"
        
        # --- THÔNG SỐ VÁN ĐẤU ---
        self.player_score = 0
        self.bot_score = 0
        self.color = "WHITE"
        self.bot_level = 1 
        self.engine = None
        self.is_bot_thinking = False
        
        # --- LUẬT CHƠI & QUYỀN LỢI ---
        self.undo_count = 3
        self.hint_count = 5 # <--- BỔ SUNG SỐ LẦN HINT
        self.hint_move = None
        self.my_time = 300.0
        self.bot_time = 300.0
        self.last_tick = time.time()
        self.timeout_sent = False
        
        # --- BÀN CỜ LOGIC ---
        self.board = chess.Board()
        self.board_state = [['' for _ in range(8)] for _ in range(8)]
        self.selected_square = None
        self.possible_moves = []
        
        self.dragging = False
        self.drag_piece = ''
        self.drag_start_pos = None 

        # --- TRẠNG THÁI END GAME ---
        self.end_state = None
        self.score_updated = False
        self.overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))

        self.piece_images = {}
        
        self.promotion_pending = None
        self.promo_rects = {}
        
        # ---> [VÁ LỖI HIỂN THỊ]: Gọi hàm này cuối cùng để chốt tọa độ 4 nút Phong cấp! <---
        self.update_layout()

    def load_scaled_image(self, path, size):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except:
            s = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 100, 100), s.get_rect(), border_radius=5)
            return s

    def load_pieces(self):
        size_kq = (int(self.sq_size * 0.9), int(self.sq_size * 0.9))
        size_rnb = (int(self.sq_size * 0.85), int(self.sq_size * 0.85))
        size_p = (int(self.sq_size * 0.75), int(self.sq_size * 0.75))
        pieces = ['bB', 'bK', 'bN', 'bP', 'bQ', 'bR', 'wB', 'wK', 'wN', 'wP', 'wQ', 'wR']
        for p in pieces:
            size = size_kq if 'K' in p or 'Q' in p else (size_p if 'P' in p else size_rnb)
            try: self.piece_images[p] = pygame.transform.smoothscale(pygame.image.load(f"assets/{p}.png").convert_alpha(), size)
            except: pass

    def update_layout(self):
        w, h = self.surface.get_size()
        cx, cy = w // 2, h // 2
        self.gap = h // 32
        
        self.overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))
        
        # ==========================================
        # 1. LAYOUT MÀN HÌNH CHỌN LEVEL (LEVEL_SELECT)
        # ==========================================
        self.back_w, self.back_h = w // 8, int((w // 8) / 4.2)
        self.back_rect = pygame.Rect(20, 20, self.back_w, self.back_h)
        
        self.lv_btn_w = int(w * 2 / 11)
        self.lv_btn_h = int(h * 5 / 11)
        lv_gap = (w - (5 * self.lv_btn_w)) // 6
        
        self.level_rects = []
        start_x = lv_gap
        for i in range(5):
            rect = pygame.Rect(start_x, cy - self.lv_btn_h // 2, self.lv_btn_w, self.lv_btn_h)
            self.level_rects.append(rect)
            start_x += self.lv_btn_w + lv_gap
            
        self.img_lvs = []
        self.img_lvs_h = []
        for i in range(1, 6):
            self.img_lvs.append(self.load_scaled_image(f"assets/btn_lv{i}.png", (self.lv_btn_w, self.lv_btn_h)))
            self.img_lvs_h.append(self.load_scaled_image(f"assets/btn_lv{i}_hover.png", (self.lv_btn_w, self.lv_btn_h)))

        # ==========================================
        # 2. LAYOUT MÀN HÌNH CHƠI CỜ (PLAYING)
        # ==========================================
        # ---> [VÁ LỖI CHỐNG TRÀN MÀN HÌNH]: Tính toán kích thước bàn cờ dựa vào CẢ chiều rộng và chiều cao!
        max_board_w = int(w * 0.65) # Dành không gian cho bảng điểm bên phải
        max_board_h = h - (2 * self.gap)
        self.board_size = min(max_board_w, max_board_h) # Cứ chọn cái nào nhỏ hơn để thu vừa khít
        
        self.board_rect = pygame.Rect(self.gap, self.gap, self.board_size, self.board_size)
        self.sq_size = self.board_size // 8
        self.load_pieces()

        score_x = self.board_rect.right + self.gap
        score_w = w - score_x - self.gap
        score_h = (h // 2) - self.gap
        self.score_rect = pygame.Rect(score_x, self.gap, score_w, score_h)
        self.img_panel_score = self.load_scaled_image("assets/panel_score.png", (score_w, score_h))

        action_area_y = self.score_rect.bottom + self.gap
        action_area_h = h - action_area_y - self.gap
        
        self.act_btn_w = int(score_w * 0.8)
        self.act_btn_h = int(self.act_btn_w / 4.2)
        half_btn_w = int(self.act_btn_w * 0.48)
        
        surrender_y = action_area_y + (action_area_h // 4) - (self.act_btn_h // 2)
        self.surrender_rect = pygame.Rect(score_x + (score_w - self.act_btn_w)//2, surrender_y, self.act_btn_w, self.act_btn_h)
        
        row2_y = action_area_y + (action_area_h * 3 // 4) - (self.act_btn_h // 2)
        self.undo_rect = pygame.Rect(self.surrender_rect.left, row2_y, half_btn_w, self.act_btn_h)
        self.hint_rect = pygame.Rect(self.surrender_rect.right - half_btn_w, row2_y, half_btn_w, self.act_btn_h)

        # Khung phong cấp đã được lấy tọa độ chuẩn xác vì board_size đã chính xác
        promo_btn_size = self.board_size // 7
        self.promo_rects = {
            'q': pygame.Rect(self.board_rect.centerx - promo_btn_size, self.board_rect.centery - promo_btn_size, promo_btn_size, promo_btn_size),
            'r': pygame.Rect(self.board_rect.centerx, self.board_rect.centery - promo_btn_size, promo_btn_size, promo_btn_size),
            'n': pygame.Rect(self.board_rect.centerx - promo_btn_size, self.board_rect.centery, promo_btn_size, promo_btn_size),
            'b': pygame.Rect(self.board_rect.centerx, self.board_rect.centery, promo_btn_size, promo_btn_size)
        }

        # --- NẠP ẢNH CƠ BẢN ---
        self.bg_game = self.load_scaled_image("assets/game_bg.png", (w, h))
        self.img_back = self.load_scaled_image("assets/btn_back.png", (self.back_w, self.back_h))
        self.img_back_h = self.load_scaled_image("assets/btn_back_hover.png", (self.back_w, self.back_h))
        
        self.img_surrender = self.load_scaled_image("assets/btn_surrender.png", (self.act_btn_w, self.act_btn_h))
        self.img_surrender_h = self.load_scaled_image("assets/btn_surrender_hover.png", (self.act_btn_w, self.act_btn_h))
        
        self.img_undo = self.load_scaled_image("assets/btn_undo.png", (half_btn_w, self.act_btn_h))
        self.img_undo_h = self.load_scaled_image("assets/btn_undo_hover.png", (half_btn_w, self.act_btn_h))
        self.img_hint = self.load_scaled_image("assets/btn_hint.png", (half_btn_w, self.act_btn_h))
        self.img_hint_h = self.load_scaled_image("assets/btn_hint_hover.png", (half_btn_w, self.act_btn_h))

        # Panel Kết thúc
        panel_w, panel_h = w // 3, int(h * 0.4)
        self.img_panel_win = self.load_scaled_image("assets/panel_win.png", (panel_w, panel_h))
        self.img_panel_loss = self.load_scaled_image("assets/panel_loss.png", (panel_w, panel_h))
        self.img_panel_draw = self.load_scaled_image("assets/panel_draw.png", (panel_w, panel_h))
        
        btn_size = (panel_w // 4, panel_h // 7)
        self.img_btn_rematch = self.load_scaled_image("assets/btn_rematch.png", btn_size)
        self.img_btn_rematch_h = self.load_scaled_image("assets/btn_rematch_hover.png", btn_size)
        self.img_btn_menu = self.load_scaled_image("assets/btn_menu.png", btn_size)
        self.img_btn_menu_h = self.load_scaled_image("assets/btn_menu_hover.png", btn_size)
        
        btn_y = cy + panel_h // 2 + (h // 64)
        self.end_btn1_rect = pygame.Rect(0, 0, btn_size[0], btn_size[1])
        self.end_btn1_rect.centerx = (cx - panel_w // 2) + (panel_w // 4)
        self.end_btn1_rect.top = btn_y
        
        self.end_btn2_rect = pygame.Rect(0, 0, btn_size[0], btn_size[1])
        self.end_btn2_rect.centerx = (cx + panel_w // 2) - (panel_w // 4)
        self.end_btn2_rect.top = btn_y

        font_size = max(25, h // 25)
        self.font = pygame.font.SysFont("segoeui", font_size, bold=True)
        self.font_score = pygame.font.SysFont("segoeui", font_size * 2, bold=True)

    def init_engine(self):
        if self.engine: self.engine.quit()
        try:
            thuat_toan_an = 0x08000000 if sys.platform == "win32" else 0
            self.engine = chess.engine.SimpleEngine.popen_uci("assets/stockfish.exe", creationflags=thuat_toan_an)
            self.engine.configure({"Skill Level": self.bot_level})
        except Exception as e:
            print(f"LỖI TẢI STOCKFISH: {e}. Vui lòng tải file stockfish.exe!")

    def start_game(self, bot_level):
        self.bot_level = bot_level
        self.init_engine()
        self.reset_board()
        self.state = "PLAYING"

    def reset_board(self):
        self.color = random.choice(["WHITE", "BLACK"])
        self.board.reset()
        self.sync_board_state()
        self.end_state = None
        self.score_updated = False
        
        self.my_time = 300.0
        self.bot_time = 300.0
        self.last_tick = time.time()
        self.timeout_sent = False
        self.undo_count = 3
        self.hint_count = 5
        self.hint_move = None
        self.selected_square = None
        self.possible_moves = []
        self.promotion_pending = None
        
        if self.color == "BLACK":
            self.trigger_bot_move()

    def get_screen_pos(self, r, c): return (7-r, 7-c) if self.color == "BLACK" else (r, c)
    def get_board_pos(self, sr, sc): return (7-sr, 7-sc) if self.color == "BLACK" else (sr, sc)
    def pos_to_uci(self, r, c): return chr(c + 97) + str(8 - r)
    def get_square_from_mouse(self, mouse_pos):
        if not self.board_rect.collidepoint(mouse_pos): return None
        sc = (mouse_pos[0] - self.board_rect.x) // self.sq_size
        sr = (mouse_pos[1] - self.board_rect.y) // self.sq_size
        lr, lc = self.get_board_pos(sr, sc)
        return chess.square(lc, 7 - lr)
    def get_rect_from_square(self, square):
        lr = 7 - chess.square_rank(square)
        sr, sc = self.get_screen_pos(lr, chess.square_file(square))
        return pygame.Rect(self.board_rect.x + sc * self.sq_size, self.board_rect.y + sr * self.sq_size, self.sq_size, self.sq_size)
    def format_time(self, seconds):
        return f"{int(max(0, seconds)) // 60:02d}:{int(max(0, seconds)) % 60:02d}"

    def sync_board_state(self):
        for r in range(8):
            for c in range(8):
                piece = self.board.piece_at(chess.square(c, 7 - r))
                self.board_state[r][c] = ('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper() if piece else ''

    # ========================================================
    # LOGIC BOT THINKING
    # ========================================================
    def trigger_bot_move(self):
        if self.end_state or self.is_bot_thinking: return
        self.is_bot_thinking = True
        self.hint_move = None 
        threading.Thread(target=self._bot_think_thread, daemon=True).start()

    def _bot_think_thread(self):
        try:
            time_limit = 0.1 if self.bot_level < 10 else 0.5 
            result = self.engine.play(self.board, chess.engine.Limit(time=time_limit))
            if result.move in self.board.legal_moves:
                self.board.push(result.move)
                self.sync_board_state()

                if self.board.is_checkmate():
                    audio_manager.play_sfx('checkmate')
                elif self.board.is_check():
                    audio_manager.play_sfx('check')
                else:
                    audio_manager.play_sfx('move')

        except: pass
        self.is_bot_thinking = False

    def request_hint(self):
        if self.end_state or self.is_bot_thinking or self.hint_move: return
        try:
            result = self.engine.play(self.board, chess.engine.Limit(depth=10)) 
            self.hint_move = result.move
        except: pass

    # ========================================================
    # VẼ GIAO DIỆN
    # ========================================================
    def draw_board(self):
        colors = [(235, 235, 208), (119, 148, 85)]
        for r in range(8):
            for c in range(8):
                sr, sc = self.get_screen_pos(r, c)
                rect = pygame.Rect(self.board_rect.x + sc*self.sq_size, self.board_rect.y + sr*self.sq_size, self.sq_size, self.sq_size)
                pygame.draw.rect(self.surface, colors[(sr + sc) % 2], rect)

        highlight_surf = pygame.Surface((self.sq_size, self.sq_size), pygame.SRCALPHA)
        
        if self.hint_move:
            highlight_surf.fill((0, 255, 0, 100)) 
            self.surface.blit(highlight_surf, self.get_rect_from_square(self.hint_move.from_square))
            self.surface.blit(highlight_surf, self.get_rect_from_square(self.hint_move.to_square))

        if self.board.is_check():
            highlight_surf.fill((255, 0, 0, 120))
            self.surface.blit(highlight_surf, self.get_rect_from_square(self.board.king(self.board.turn)))

        if self.selected_square is not None:
            highlight_surf.fill((180, 130, 230, 150))
            self.surface.blit(highlight_surf, self.get_rect_from_square(self.selected_square))

        if self.possible_moves:
            dot_radius = self.sq_size // 6  
            for move in self.possible_moves:
                rect = self.get_rect_from_square(move.to_square)
                if self.board.is_castling(move): highlight_surf.fill((255, 255, 0, 100))
                elif self.board.is_capture(move): highlight_surf.fill((0, 0, 255, 80))
                else:
                    highlight_surf.fill((0,0,0,0))
                    pygame.draw.circle(highlight_surf, (150, 150, 150, 150), (self.sq_size//2, self.sq_size//2), dot_radius)
                self.surface.blit(highlight_surf, rect)

        for r in range(8):
            for c in range(8):
                sr, sc = self.get_screen_pos(r, c)
                rect = pygame.Rect(self.board_rect.x + sc*self.sq_size, self.board_rect.y + sr*self.sq_size, self.sq_size, self.sq_size)
                if self.dragging and getattr(self, 'drag_start_pos', None) == (r, c): continue
                piece = self.board_state[r][c]
                if piece:
                    img = self.piece_images.get(piece)
                    if img: self.surface.blit(img, img.get_rect(center=rect.center))
                        
        if self.dragging and getattr(self, 'drag_piece', '') != '':
            img = self.piece_images.get(self.drag_piece)
            if img: self.surface.blit(img, img.get_rect(center=pygame.mouse.get_pos()))
        
        if getattr(self, 'promotion_pending', None):
            dark = pygame.Surface((self.board_rect.width, self.board_rect.height), pygame.SRCALPHA)
            dark.fill((0, 0, 0, 160)) 
            self.surface.blit(dark, self.board_rect.topleft)
            m_pos = pygame.mouse.get_pos()
            
            bg_norm, bg_h, keys = ((50,50,50), (100,100,100), {'q':'wQ','r':'wR','n':'wN','b':'wB'}) if self.color == "WHITE" else ((200,200,200), (240,240,240), {'q':'bQ','r':'bR','n':'bN','b':'bB'})
            for k, rect in self.promo_rects.items():
                hov = rect.collidepoint(m_pos)
                pygame.draw.rect(self.surface, bg_h if hov else bg_norm, rect)
                pygame.draw.rect(self.surface, (255, 215, 0) if hov else (20,20,20), rect, 2)
                img = self.piece_images.get(keys[k])
                if img: self.surface.blit(img, img.get_rect(center=rect.center))

    def draw(self):
        self.surface.blit(self.bg_game, (0, 0))
        m_pos = pygame.mouse.get_pos()
        
        if self.state == "LEVEL_SELECT":
            self.surface.blit(self.img_back_h if self.back_rect.collidepoint(m_pos) else self.img_back, self.back_rect)
            
            title = self.font_score.render("CHOOSE STOCKFISH LEVEL", True, (255, 255, 255))
            self.surface.blit(title, title.get_rect(center=(self.surface.get_width()//2, self.gap * 3)))
            
            for i, rect in enumerate(self.level_rects):
                self.surface.blit(self.img_lvs_h[i] if rect.collidepoint(m_pos) else self.img_lvs[i], rect)
            return

        self.draw_board()
        
        opp_name = self.font.render(f"Stockfish (Lv {self.bot_level})", True, (255, 255, 255))
        self.surface.blit(opp_name, opp_name.get_rect(midleft=(self.board_rect.left, self.gap // 2)))
        opp_time = self.font.render(self.format_time(self.bot_time), True, (255, 255, 255))
        self.surface.blit(opp_time, opp_time.get_rect(midright=(self.board_rect.right, self.gap // 2)))

        me_name = self.font.render("Player", True, (255, 255, 255))
        self.surface.blit(me_name, me_name.get_rect(midleft=(self.board_rect.left, self.surface.get_height() - self.gap // 2)))
        me_time = self.font.render(self.format_time(self.my_time), True, (255, 255, 255))
        self.surface.blit(me_time, me_time.get_rect(midright=(self.board_rect.right, self.surface.get_height() - self.gap // 2)))

        self.surface.blit(self.img_panel_score, self.score_rect)
        score_txt = self.font_score.render(f"{self.player_score} - {self.bot_score}", True, (255, 215, 0))
        self.surface.blit(score_txt, score_txt.get_rect(center=self.score_rect.center))
        
        self.surface.blit(self.img_surrender_h if self.surrender_rect.collidepoint(m_pos) else self.img_surrender, self.surrender_rect)
        self.surface.blit(self.img_undo_h if self.undo_rect.collidepoint(m_pos) else self.img_undo, self.undo_rect)
        self.surface.blit(self.img_hint_h if self.hint_rect.collidepoint(m_pos) else self.img_hint, self.hint_rect)

        undo_txt = self.font.render(f"({self.undo_count}/3)", True, (200, 200, 200))
        self.surface.blit(undo_txt, undo_txt.get_rect(midbottom=(self.undo_rect.centerx, self.undo_rect.top - 5)))

        hint_txt = self.font.render(f"({self.hint_count}/5)", True, (200, 200, 200))
        self.surface.blit(hint_txt, hint_txt.get_rect(midbottom=(self.hint_rect.centerx, self.hint_rect.top - 5)))

        if self.end_state:
            self.surface.blit(self.overlay, (0, 0))
            cx, cy = self.surface.get_width() // 2, self.surface.get_height() // 2
            
            panel = self.img_panel_win if self.end_state == "WIN" else (self.img_panel_draw if self.end_state == "DRAW" else self.img_panel_loss)
            self.surface.blit(panel, panel.get_rect(center=(cx, cy)))
            
            self.surface.blit(self.img_btn_rematch_h if self.end_btn1_rect.collidepoint(m_pos) else self.img_btn_rematch, self.end_btn1_rect)
            self.surface.blit(self.img_btn_menu_h if self.end_btn2_rect.collidepoint(m_pos) else self.img_btn_menu, self.end_btn2_rect)


def run(screen):

    ui = SinglePlayUI(screen)
    clock = pygame.time.Clock()
    
    levels = [1, 5, 10, 15, 20] 

    while True:
        if ui.state == "PLAYING" and not ui.end_state:
            if ui.board.is_game_over():
                res = ui.board.result()
                if res == "1/2-1/2": 
                    ui.end_state = "DRAW"
                    audio_manager.play_sfx('draw') 
                elif (res == "1-0" and ui.color == "WHITE") or (res == "0-1" and ui.color == "BLACK"): 
                    ui.end_state = "WIN"
                    audio_manager.play_sfx('win')  
                else: 
                    ui.end_state = "LOSS"
                    audio_manager.play_sfx('lose') 

        if ui.end_state and not ui.score_updated:
            if ui.end_state == "WIN": ui.player_score += 1
            elif ui.end_state == "LOSS": ui.bot_score += 1
            ui.score_updated = True

        if ui.state == "PLAYING" and not ui.end_state:
            dt = time.time() - ui.last_tick
            ui.last_tick = time.time()
            
            is_my_turn = (ui.board.turn == chess.WHITE and ui.color == "WHITE") or (ui.board.turn == chess.BLACK and ui.color == "BLACK")
            
            if is_my_turn:
                ui.my_time -= dt
                if ui.my_time <= 0:
                    ui.my_time = 0
                    ui.end_state = "LOSS"
                    audio_manager.play_sfx('lose') 
            else:
                ui.bot_time -= dt
                if ui.bot_time <= 0:
                    ui.bot_time = 0
                    ui.end_state = "WIN"
                    audio_manager.play_sfx('win') 
        else:
            ui.last_tick = time.time()

        ui.draw()
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                if ui.engine: ui.engine.quit()
                pygame.quit(); sys.exit()
                
            elif e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                ui.surface = screen
                ui.update_layout()
                
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = e.pos

                if ui.state == "LEVEL_SELECT":
                    if ui.back_rect.collidepoint(mouse_pos):
                        audio_manager.play_sfx('click') 
                        return "BACK"
                    for i, rect in enumerate(ui.level_rects):
                        if rect.collidepoint(mouse_pos):
                            audio_manager.play_sfx('click') 
                            ui.start_game(levels[i])
                    continue

                if ui.end_state:
                    if ui.end_btn1_rect.collidepoint(mouse_pos): 
                        audio_manager.play_sfx('click') 
                        ui.reset_board()
                    elif ui.end_btn2_rect.collidepoint(mouse_pos): 
                        audio_manager.play_sfx('click') 
                        if ui.engine: ui.engine.quit()
                        return "BACK_TO_MENU"
                    continue

                is_my_turn = (ui.board.turn == chess.WHITE and ui.color == "WHITE") or (ui.board.turn == chess.BLACK and ui.color == "BLACK")
                
                if ui.surrender_rect.collidepoint(mouse_pos):
                    audio_manager.play_sfx('click') 
                    ui.end_state = "LOSS"
                    audio_manager.play_sfx('lose') 
                    continue
                    
                if ui.undo_rect.collidepoint(mouse_pos) and is_my_turn and ui.undo_count > 0 and len(ui.board.move_stack) >= 2:
                    audio_manager.play_sfx('click') 
                    ui.board.pop() 
                    ui.board.pop() 
                    ui.undo_count -= 1
                    ui.sync_board_state()
                    ui.selected_square = None
                    ui.possible_moves = []
                    ui.hint_move = None
                    continue
                    
                if ui.hint_rect.collidepoint(mouse_pos) and is_my_turn:
                    audio_manager.play_sfx('click') 
                    if ui.hint_count > 0 and not ui.hint_move: 
                        ui.request_hint()
                        ui.hint_count -= 1 
                    continue

                # ==========================================
                # ---> [VÁ LỖI TẠI ĐÂY]: XỬ LÝ CLICK BẢNG PHONG CẤP <---
                if ui.promotion_pending:
                    if ui.board_rect.collidepoint(mouse_pos):
                        for key, rect in ui.promo_rects.items():
                            if rect.collidepoint(mouse_pos):
                                move = chess.Move.from_uci(ui.promotion_pending + key)
                                ui.board.push(move)
                                ui.sync_board_state()
                                ui.promotion_pending = None
                                
                                if ui.board.is_checkmate(): audio_manager.play_sfx('checkmate')
                                elif ui.board.is_check(): audio_manager.play_sfx('check')
                                else: audio_manager.play_sfx('move')
                                
                                ui.trigger_bot_move() 
                                break
                        if ui.promotion_pending and not any(r.collidepoint(mouse_pos) for r in ui.promo_rects.values()):
                            ui.promotion_pending = None
                            ui.selected_square = None
                            ui.possible_moves = []
                        continue

                # ==========================================
                # ---> [VÁ LỖI TẠI ĐÂY]: BỘ LỌC CHỐNG CRASH KHI PRE-MOVE (TAP) <---
                clicked_square = ui.get_square_from_mouse(mouse_pos)
                if clicked_square is not None:
                    my_chess_color = chess.WHITE if ui.color == "WHITE" else chess.BLACK
                    
                    if ui.selected_square == clicked_square:
                        ui.selected_square = None
                        ui.possible_moves = []
                    elif ui.board.piece_at(clicked_square) and ui.board.piece_at(clicked_square).color == my_chess_color:
                        ui.selected_square = clicked_square
                        ui.possible_moves = [m for m in ui.board.legal_moves if m.from_square == clicked_square]
                        lr, lc = 7 - chess.square_rank(clicked_square), chess.square_file(clicked_square)
                        ui.dragging = True
                        ui.drag_piece = ui.board_state[lr][lc]
                        ui.drag_start_pos = (lr, lc)
                    elif ui.selected_square is not None:
                        if ui.drag_start_pos is not None:
                            lr, lc = 7 - chess.square_rank(clicked_square), chess.square_file(clicked_square)
                            uci_str = ui.pos_to_uci(ui.drag_start_pos[0], ui.drag_start_pos[1]) + ui.pos_to_uci(lr, lc)
                            
                            # Bộ lọc kiểm tra tính hợp lệ trước khi quyết định hiện bảng phong cấp hay đi cờ
                            try: test_promo = chess.Move.from_uci(uci_str + 'q')
                            except: test_promo = None
                            
                            try: test_normal = chess.Move.from_uci(uci_str)
                            except: test_normal = None

                            if ui.drag_piece.endswith('P') and (lr == 0 or lr == 7) and (test_promo in ui.board.legal_moves): 
                                ui.promotion_pending = uci_str
                            elif test_normal in ui.board.legal_moves:
                                move = chess.Move.from_uci(uci_str)
                                ui.board.push(move)
                                ui.sync_board_state()
                                
                                if ui.board.is_checkmate(): audio_manager.play_sfx('checkmate')
                                elif ui.board.is_check(): audio_manager.play_sfx('check')
                                else: audio_manager.play_sfx('move')
                                
                                ui.trigger_bot_move() 
                        ui.selected_square = None
                        ui.possible_moves = []
                        ui.dragging = False
                        ui.drag_piece = ''
                        ui.drag_start_pos = None

            # ==========================================
            # ---> [VÁ LỖI TẠI ĐÂY]: BỘ LỌC CHỐNG CRASH KHI PRE-MOVE (DRAG&DROP) <---
            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if ui.dragging:
                    mouse_pos = e.pos
                    if ui.board_rect.collidepoint(mouse_pos):
                        sc, sr = (mouse_pos[0] - ui.board_rect.x) // ui.sq_size, (mouse_pos[1] - ui.board_rect.y) // ui.sq_size
                        tr, tc = ui.get_board_pos(sr, sc)
                        if (tr, tc) != ui.drag_start_pos:
                            uci_str = ui.pos_to_uci(ui.drag_start_pos[0], ui.drag_start_pos[1]) + ui.pos_to_uci(tr, tc)
                            
                            # Bộ lọc kiểm tra tính hợp lệ
                            try: test_promo = chess.Move.from_uci(uci_str + 'q')
                            except: test_promo = None
                            
                            try: test_normal = chess.Move.from_uci(uci_str)
                            except: test_normal = None

                            if ui.drag_piece.endswith('P') and (tr == 0 or tr == 7) and (test_promo in ui.board.legal_moves): 
                                ui.promotion_pending = uci_str
                            elif test_normal in ui.board.legal_moves: 
                                move = chess.Move.from_uci(uci_str)
                                ui.board.push(move)
                                ui.sync_board_state()
                                
                                if ui.board.is_checkmate(): audio_manager.play_sfx('checkmate')
                                elif ui.board.is_check(): audio_manager.play_sfx('check')
                                else: audio_manager.play_sfx('move')
                                
                                ui.trigger_bot_move()
                        ui.selected_square = None
                        ui.possible_moves = []
                        ui.dragging = False
                        ui.drag_piece = ''
                        ui.drag_start_pos = None
                    else: ui.dragging = False
                else:
                    ui.dragging = False
                    ui.selected_square = None
                    ui.possible_moves = []

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    audio_manager.play_sfx('click') 
                    if ui.engine: ui.engine.quit()
                    return "BACK_TO_MENU"

        pygame.display.flip()
        clock.tick(60)