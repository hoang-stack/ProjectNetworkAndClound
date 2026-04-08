import pygame
import sys
import time
import chess
import audio_manager
import json


class GamePlayUI:
    def __init__(self, surface, player_name, opponent_name, net, color):
        self.surface = surface
        self.player_name = player_name
        self.opponent_name = opponent_name
        self.net = net
        self.color = color 
        
        self.chat_messages = ["Hệ thống: Trận đấu bắt đầu!"]
        self.chat_input = ""
        self.input_active = False

        # --- QUẢN LÝ KẾT THÚC TRẬN & REMATCH ---
        self.end_state = None       # Các giá trị: None, "WIN", "LOSS", "DRAW"
        self.rematch_status = "IDLE"# Các giá trị: "IDLE", "WAITING", "RECEIVED"
        self.draw_offer_status = None # CÁC TRẠNG THÁI: "WAITING", "RECEIVED", "DECLINED"
        self.overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180)) # Nền kính râm tối lại 180/255

        self.dragging = False
        self.drag_piece = ''
        self.drag_start_pos = None 

        # ---> BỔ SUNG BIẾN THỜI GIAN (5 PHÚT = 300 GIÂY) <---
        self.my_time = 300.0
        self.opp_time = 300.0
        self.last_tick = time.time()
        self.timeout_sent = False

        # BÀN CỜ GỐC
        self.board_state = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]

        self.board = chess.Board() # Bàn cờ ảo để tính toán luật chơi
        self.selected_square = None
        self.possible_moves = []
        
        self.piece_images = {}

        self.promotion_pending = None # Chờ người chơi chọn quân phong cấp
        self.promo_rects = {}
        self.rematch_timer_start = 0
        self.draw_timer_start = 0
        self.update_layout()
        
    def get_screen_pos(self, r, c):
        if self.color == "BLACK": return 7 - r, 7 - c
        return r, c

    def get_board_pos(self, screen_r, screen_c):
        if self.color == "BLACK": return 7 - screen_r, 7 - screen_c
        return screen_r, screen_c

    def pos_to_uci(self, r, c):
        return chr(c + 97) + str(8 - r)

    def uci_to_pos(self, uci):
        col = ord(uci[0]) - 97
        row = 8 - int(uci[1])
        return row, col
    
    def format_time(self, seconds):
        if seconds < 0: seconds = 0
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m:02d}:{s:02d}"
    
    def get_square_from_mouse(self, mouse_pos):
        if not self.board_rect.collidepoint(mouse_pos):
            return None
        screen_c = (mouse_pos[0] - self.board_rect.x) // self.sq_size
        screen_r = (mouse_pos[1] - self.board_rect.y) // self.sq_size
        logical_r, logical_c = self.get_board_pos(screen_r, screen_c)
        return chess.square(logical_c, 7 - logical_r)

    def get_rect_from_square(self, square):
        logical_c = chess.square_file(square)
        logical_r = 7 - chess.square_rank(square)
        screen_r, screen_c = self.get_screen_pos(logical_r, logical_c)
        x = self.board_rect.x + screen_c * self.sq_size
        y = self.board_rect.y + screen_r * self.sq_size
        return pygame.Rect(x, y, self.sq_size, self.sq_size)

    def reset_board(self):
        self.board_state = [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]
        self.end_state = None
        self.rematch_status = "IDLE"
        self.chat_messages.append("Hệ thống: Bắt đầu ván mới!")
        self.board.reset()
        self.my_time = 300.0
        self.opp_time = 300.0
        self.last_tick = time.time()
        self.timeout_sent = False
        
    def sync_board_state(self):
        for r in range(8):
            for c in range(8):
                square = chess.square(c, 7 - r)
                piece = self.board.piece_at(square)
                if piece:
                    color = 'w' if piece.color == chess.WHITE else 'b'
                    symbol = piece.symbol().upper()
                    self.board_state[r][c] = color + symbol
                else:
                    self.board_state[r][c] = ''

    def load_scaled_image(self, path, size):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except:
            s = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 100, 100), s.get_rect(), border_radius=5)
            return s

    def load_pieces(self):
        size_kq = (int(self.board_size / 8), int(self.board_size / 8))
        size_rnb = (int(self.board_size / 8.2), int(self.board_size / 8.2))
        size_p = (int(self.board_size / 9), int(self.board_size / 9))
        pieces = ['bB', 'bK', 'bN', 'bP', 'bQ', 'bR', 'wB', 'wK', 'wN', 'wP', 'wQ', 'wR']
        for p in pieces:
            size = size_kq if 'K' in p or 'Q' in p else (size_p if 'P' in p else size_rnb)
            try: self.piece_images[p] = pygame.transform.smoothscale(pygame.image.load(f"assets/{p}.png").convert_alpha(), size)
            except: 
                s = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.circle(s, (200,50,50) if p[0]=='w' else (50,50,50), (size[0]//2, size[1]//2), size[0]//2)
                self.piece_images[p] = s

    def update_layout(self):
        w, h = self.surface.get_size()
        self.gap = h // 32
        
        max_board_w = int(w * 0.65) # Dành không gian cho chat
        max_board_h = h - (2 * self.gap)
        self.board_size = min(max_board_w, max_board_h) # Luôn lấy size nhỏ hơn để vừa khít
        
        self.board_rect = pygame.Rect(self.gap, self.gap, self.board_size, self.board_size)
        self.sq_size = self.board_size // 8
        self.load_pieces()

        right_panel_x = self.board_rect.right + self.gap
        right_panel_w = w - right_panel_x - self.gap 

        chat_h = (h * 3) // 5 
        self.chat_rect = pygame.Rect(right_panel_x, h - self.gap - chat_h, right_panel_w, chat_h)
        self.chat_input_rect = pygame.Rect(self.chat_rect.x + 10, self.chat_rect.bottom - 45, self.chat_rect.width - 20, 35)

        self.btn_w = w // 4
        self.btn_h = int(self.btn_w / 4.2)
        top_space_h = self.chat_rect.top - self.gap 
        total_btn_h = self.btn_h * 2 + self.gap 
        btn_x = right_panel_x + (right_panel_w - self.btn_w) // 2
        start_y = self.gap + (top_space_h - total_btn_h) // 2
        
        self.surrender_rect = pygame.Rect(btn_x, start_y, self.btn_w, self.btn_h)
        self.draw_rect = pygame.Rect(btn_x, start_y + self.btn_h + self.gap, self.btn_w, self.btn_h)

       # ---------------- NẠP ẢNH GIAO DIỆN KẾT THÚC ----------------
        self.overlay = pygame.transform.scale(self.overlay, (w, h))
        
        panel_w = w // 3
        panel_h = int(h * 0.4)
        panel_size = (panel_w, panel_h) 
        
        self.img_panel_win = self.load_scaled_image("assets/panel_win.png", panel_size)
        self.img_panel_loss = self.load_scaled_image("assets/panel_loss.png", panel_size)
        self.img_panel_rematch = self.load_scaled_image("assets/panel_rematch.png", panel_size)
        self.img_panel_draw = self.load_scaled_image("assets/panel_draw.png", panel_size)
        self.img_panel_offer = self.load_scaled_image("assets/panel_offer.png", panel_size)
        self.img_panel_declined = self.load_scaled_image("assets/panel_declined.png", panel_size)
        self.img_panel_disconnect = self.load_scaled_image("assets/panel_disconnect.png", panel_size)

        end_btn_w = panel_w // 4
        end_btn_h = panel_h // 7
        btn_size = (end_btn_w, end_btn_h)
        
        self.img_btn_rematch = self.load_scaled_image("assets/btn_rematch.png", btn_size)
        self.img_btn_rematch_h = self.load_scaled_image("assets/btn_rematch_hover.png", btn_size)
        self.img_btn_menu = self.load_scaled_image("assets/btn_menu.png", btn_size)
        self.img_btn_menu_h = self.load_scaled_image("assets/btn_menu_hover.png", btn_size)
        self.img_btn_ok = self.load_scaled_image("assets/btn_ok.png", btn_size)
        self.img_btn_ok_h = self.load_scaled_image("assets/btn_ok_hover.png", btn_size)
        self.img_btn_decline = self.load_scaled_image("assets/btn_decline.png", btn_size)
        self.img_btn_decline_h = self.load_scaled_image("assets/btn_decline_hover.png", btn_size)
        self.img_btn_wait = self.load_scaled_image("assets/btn_wait.png", btn_size)
        self.img_btn_wait_h = self.load_scaled_image("assets/btn_wait_hover.png", btn_size)
        self.img_loading = self.load_scaled_image("assets/loading.png", (h // 12, h // 12))

        cx, cy = w // 2, h // 2
        panel_left = cx - panel_w // 2
        panel_right = cx + panel_w // 2
        panel_bottom = cy + panel_h // 2
        end_gap = h // 64
        btn_y = panel_bottom + end_gap
        
        self.end_btn1_rect = pygame.Rect(0, 0, end_btn_w, end_btn_h)
        self.end_btn1_rect.centerx = panel_left + (panel_w // 4)
        self.end_btn1_rect.top = btn_y
        
        self.end_btn2_rect = pygame.Rect(0, 0, end_btn_w, end_btn_h)
        self.end_btn2_rect.centerx = panel_right - (panel_w // 4)
        self.end_btn2_rect.top = btn_y

        self.center_btn_rect = pygame.Rect(0, 0, end_btn_w, end_btn_h)
        self.center_btn_rect.centerx = cx
        self.center_btn_rect.top = btn_y

        # ---------------- NẠP ẢNH CƠ BẢN ----------------
        self.bg_game = self.load_scaled_image("assets/game_bg.png", (w, h))
        self.img_surrender = self.load_scaled_image("assets/btn_surrender.png", (self.btn_w, self.btn_h))
        self.img_surrender_h = self.load_scaled_image("assets/btn_surrender_hover.png", (self.btn_w, self.btn_h))
        self.img_draw = self.load_scaled_image("assets/btn_draw.png", (self.btn_w, self.btn_h))
        self.img_draw_h = self.load_scaled_image("assets/btn_draw_hover.png", (self.btn_w, self.btn_h))

        font_size = max(18, h // 35)
        font_size_small = max(14, h // 45)
        try: 
            self.font = pygame.font.SysFont("segoeui", font_size, bold=True)
            self.font_small = pygame.font.SysFont("segoeui", font_size_small)
        except: 
            self.font = pygame.font.SysFont("tahoma", font_size, bold=True)
            self.font_small = pygame.font.SysFont("tahoma", font_size_small)
        
        promo_btn_size = self.board_size // 7
        cx_board = self.board_rect.centerx
        cy_board = self.board_rect.centery
        
        self.promo_rects = {
            'q': pygame.Rect(cx_board - promo_btn_size, cy_board - promo_btn_size, promo_btn_size, promo_btn_size),
            'r': pygame.Rect(cx_board, cy_board - promo_btn_size, promo_btn_size, promo_btn_size),
            'n': pygame.Rect(cx_board - promo_btn_size, cy_board, promo_btn_size, promo_btn_size),
            'b': pygame.Rect(cx_board, cy_board, promo_btn_size, promo_btn_size)
        }

    def draw_board(self):
        colors = [(235, 235, 208), (119, 148, 85)]
        
        # 1: VẼ NỀN BÀN CỜ
        for logical_r in range(8):
            for logical_c in range(8):
                screen_r, screen_c = self.get_screen_pos(logical_r, logical_c)
                color = colors[(screen_r + screen_c) % 2]
                rect = pygame.Rect(self.board_rect.x + screen_c*self.sq_size, 
                                   self.board_rect.y + screen_r*self.sq_size, 
                                   self.sq_size, self.sq_size)
                pygame.draw.rect(self.surface, color, rect)

        # 2: VẼ HIGHLIGHT & GỢI Ý
        COLOR_HINT_DOT = (150, 150, 150, 150) 
        COLOR_HINT_CAPTURE = (0, 0, 255, 80) 
        COLOR_HINT_CASTLING = (255, 255, 0, 100) 
        COLOR_HINT_CHECK = (255, 0, 0, 120) 
        
        highlight_surf = pygame.Surface((self.sq_size, self.sq_size), pygame.SRCALPHA)
        
        if self.board.is_check():
            king_square = self.board.king(self.board.turn)
            rect = self.get_rect_from_square(king_square)
            highlight_surf.fill(COLOR_HINT_CHECK)
            self.surface.blit(highlight_surf, rect)

        if self.selected_square is not None:
            rect = self.get_rect_from_square(self.selected_square)
            highlight_surf.fill((180, 130, 230, 150))
            self.surface.blit(highlight_surf, rect)

        if getattr(self, 'possible_moves', None):
            dot_radius = self.sq_size // 6  
            for move in self.possible_moves:
                to_sq = move.to_square
                rect = self.get_rect_from_square(to_sq)
                if self.board.is_castling(move):
                    highlight_surf.fill(COLOR_HINT_CASTLING)
                    self.surface.blit(highlight_surf, rect)
                elif self.board.is_capture(move):
                    highlight_surf.fill(COLOR_HINT_CAPTURE)
                    self.surface.blit(highlight_surf, rect)
                else:
                    center_pos = rect.center
                    dot_surf = pygame.Surface((dot_radius*2, dot_radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(dot_surf, COLOR_HINT_DOT, (dot_radius, dot_radius), dot_radius)
                    self.surface.blit(dot_surf, (center_pos[0] - dot_radius, center_pos[1] - dot_radius))

        # 3: VẼ QUÂN CỜ ĐÈ LÊN TRÊN CÙNG
        for logical_r in range(8):
            for logical_c in range(8):
                screen_r, screen_c = self.get_screen_pos(logical_r, logical_c)
                rect = pygame.Rect(self.board_rect.x + screen_c*self.sq_size, 
                                   self.board_rect.y + screen_r*self.sq_size, 
                                   self.sq_size, self.sq_size)
                
                if self.dragging and getattr(self, 'drag_start_pos', None) == (logical_r, logical_c): 
                    continue

                piece = self.board_state[logical_r][logical_c]
                if piece != '':
                    img = self.piece_images.get(piece)
                    if img: self.surface.blit(img, img.get_rect(center=rect.center))
                        
        if self.dragging and getattr(self, 'drag_piece', '') != '':
            img = self.piece_images.get(self.drag_piece)
            if img: self.surface.blit(img, img.get_rect(center=pygame.mouse.get_pos()))
        
        # 4: BẢNG CHỌN PHONG CẤP
        if getattr(self, 'promotion_pending', None):
            dark_surf = pygame.Surface((self.board_rect.width, self.board_rect.height), pygame.SRCALPHA)
            dark_surf.fill((0, 0, 0, 160)) 
            self.surface.blit(dark_surf, self.board_rect.topleft)
            m_pos = pygame.mouse.get_pos()
            
            if self.color == "WHITE":
                bg_norm, bg_hover, p_keys = (50, 50, 50), (100, 100, 100), {'q': 'wQ', 'r': 'wR', 'n': 'wN', 'b': 'wB'}
            else:
                bg_norm, bg_hover, p_keys = (200, 200, 200), (240, 240, 240), {'q': 'bQ', 'r': 'bR', 'n': 'bN', 'b': 'bB'}
                
            for key, rect in self.promo_rects.items():
                is_hover = rect.collidepoint(m_pos)
                pygame.draw.rect(self.surface, bg_hover if is_hover else bg_norm, rect)
                pygame.draw.rect(self.surface, (255, 215, 0) if is_hover else (20,20,20), rect, 2)
                img = self.piece_images.get(p_keys[key])
                if img: self.surface.blit(img, img.get_rect(center=rect.center))
        
    def draw_chat(self):
        s = pygame.Surface((self.chat_rect.width, self.chat_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 20, 20, 200), s.get_rect(), border_radius=12)
        self.surface.blit(s, self.chat_rect.topleft)
        pygame.draw.rect(self.surface, (100, 100, 100), self.chat_rect, 2, border_radius=12)

        border_color = (0, 255, 255) if self.input_active else (80, 80, 80)
        pygame.draw.rect(self.surface, (40, 40, 40), self.chat_input_rect, border_radius=8)
        pygame.draw.rect(self.surface, border_color, self.chat_input_rect, 2, border_radius=8)
        
        display_txt = self.chat_input + ("|" if self.input_active and (pygame.time.get_ticks() // 500) % 2 else "")
        if display_txt == "" and not self.input_active:
            txt_surf = self.font_small.render("Type a message...", True, (150, 150, 150))
        else:
            txt_surf = self.font_small.render(display_txt, True, (255, 255, 255))
        self.surface.blit(txt_surf, (self.chat_input_rect.x + 8, self.chat_input_rect.y + (self.chat_input_rect.height - txt_surf.get_height())//2))

        y_offset = self.chat_input_rect.top - 10
        max_msgs = (self.chat_rect.height - 60) // 25
        for msg in reversed(self.chat_messages[-max_msgs:]):
            msg_surf = self.font_small.render(msg, True, (220, 220, 220))
            y_offset -= msg_surf.get_height() + 5
            self.surface.blit(msg_surf, (self.chat_rect.x + 10, y_offset))

    def draw_end_game_overlay(self):
        cx, cy = self.surface.get_width() // 2, self.surface.get_height() // 2
        m_pos = pygame.mouse.get_pos()
        def draw_btn(rect, img_norm, img_hover):
            self.surface.blit(img_hover if rect.collidepoint(m_pos) else img_norm, rect)

        # LỚP PHỦ XIN HÒA
        if self.draw_offer_status:
            self.surface.blit(self.overlay, (0, 0)) 
            remain = max(0, 15 - int(time.time() - getattr(self, 'draw_timer_start', time.time())))
            
            if self.draw_offer_status == "WAITING":
                txt_surf = self.font.render(f"Đang đợi đối thủ phản hồi cầu hòa... ({remain}s)", True, (255, 255, 255))
                self.surface.blit(txt_surf, txt_surf.get_rect(center=(cx, cy - 40)))
                angle = (pygame.time.get_ticks() // 10) % 360
                rotated = pygame.transform.rotate(self.img_loading, -angle)
                self.surface.blit(rotated, rotated.get_rect(center=(cx, cy + 30)))
                
            elif self.draw_offer_status == "RECEIVED":
                self.surface.blit(self.img_panel_offer, self.img_panel_offer.get_rect(center=(cx, cy)))
                txt_surf = self.font.render(f"Tự động từ chối sau: {remain}s", True, (255, 100, 100))
                self.surface.blit(txt_surf, txt_surf.get_rect(center=(cx, cy - self.img_panel_offer.get_height()//2 - 20)))
                draw_btn(self.end_btn1_rect, self.img_btn_ok, self.img_btn_ok_h)
                draw_btn(self.end_btn2_rect, self.img_btn_decline, self.img_btn_decline_h) 
                
            elif self.draw_offer_status == "DECLINED":
                self.surface.blit(self.img_panel_declined, self.img_panel_declined.get_rect(center=(cx, cy)))
                draw_btn(self.center_btn_rect, self.img_btn_ok, self.img_btn_ok_h)
            return

        # LỚP PHỦ KẾT THÚC GAME
        if not self.end_state: return

        self.surface.blit(self.overlay, (0, 0))
        
        if self.rematch_status == "WAITING":
            remain = max(0, 15 - int(time.time() - self.rematch_timer_start))
            txt_surf = self.font.render(f"Đang chờ đối thủ phản hồi... ({remain}s)", True, (255, 255, 255))
            self.surface.blit(txt_surf, txt_surf.get_rect(center=(cx, cy - 40)))
            angle = (pygame.time.get_ticks() // 10) % 360
            rotated = pygame.transform.rotate(self.img_loading, -angle)
            self.surface.blit(rotated, rotated.get_rect(center=(cx, cy + 30)))
            return

        if self.rematch_status == "RECEIVED": panel_img = self.img_panel_rematch
        elif self.end_state == "SERVER_DISCONNECTED": panel_img = self.img_panel_disconnect 
        elif self.end_state == "WIN": panel_img = self.img_panel_win
        elif self.end_state == "DRAW": panel_img = self.img_panel_draw 
        else: panel_img = self.img_panel_loss 

        self.surface.blit(panel_img, panel_img.get_rect(center=(cx, cy)))

        if self.end_state == "SERVER_DISCONNECTED":
            draw_btn(self.center_btn_rect, self.img_btn_menu, self.img_btn_menu_h)
            return 
            
        elif self.rematch_status == "IDLE":
            draw_btn(self.end_btn1_rect, self.img_btn_rematch, self.img_btn_rematch_h)
            draw_btn(self.end_btn2_rect, self.img_btn_menu, self.img_btn_menu_h)
            
        elif self.rematch_status == "RECEIVED":
            draw_btn(self.end_btn1_rect, self.img_btn_ok, self.img_btn_ok_h)
            draw_btn(self.end_btn2_rect, self.img_btn_decline, self.img_btn_decline_h) 
            
        elif self.rematch_status == "OPPONENT_LEFT":
            txt_surf = self.font_small.render("Your opponent has left!", True, (255, 80, 80))
            self.surface.blit(txt_surf, txt_surf.get_rect(center=(cx, self.center_btn_rect.top - 20)))
            draw_btn(self.center_btn_rect, self.img_btn_menu, self.img_btn_menu_h)

    def draw(self):
        self.surface.blit(self.bg_game, (0, 0))
        self.draw_board()
        self.draw_chat()
        
        opp_name_txt = self.font.render(self.opponent_name, True, (255, 255, 255))
        opp_name_rect = opp_name_txt.get_rect(midleft=(self.board_rect.left, self.gap // 2))
        self.surface.blit(opp_name_txt, opp_name_rect)
        
        opp_time_txt = self.font.render(self.format_time(self.opp_time), True, (255, 255, 255))
        opp_time_rect = opp_time_txt.get_rect(midright=(self.board_rect.right, self.gap // 2))
        self.surface.blit(opp_time_txt, opp_time_rect)

        me_name_txt = self.font.render(self.player_name, True, (255, 255, 255))
        me_name_rect = me_name_txt.get_rect(midleft=(self.board_rect.left, self.surface.get_height() - self.gap // 2))
        self.surface.blit(me_name_txt, me_name_rect)
        
        me_time_txt = self.font.render(self.format_time(self.my_time), True, (255, 255, 255))
        me_time_rect = me_time_txt.get_rect(midright=(self.board_rect.right, self.surface.get_height() - self.gap // 2))
        self.surface.blit(me_time_txt, me_time_rect)

        m_pos = pygame.mouse.get_pos()
        self.surface.blit(self.img_surrender_h if self.surrender_rect.collidepoint(m_pos) else self.img_surrender, self.surrender_rect)
        self.surface.blit(self.img_draw_h if self.draw_rect.collidepoint(m_pos) else self.img_draw, self.draw_rect)

        self.draw_end_game_overlay()

def run(screen, player_name, opponent_name, net, color):
    ui = GamePlayUI(screen, player_name, opponent_name, net, color)
    clock = pygame.time.Clock()
    
    while True:
        # ---------------- NHẬN LỆNH TỪ SERVER ----------------
        messages = net.get_messages()

        for msg in messages:
            msg_type = msg.get("type")
            if msg_type == "SERVER_DISCONNECTED":
                if ui.end_state != "SERVER_DISCONNECTED":
                    audio_manager.play_sfx('notify')
                    ui.end_state = "SERVER_DISCONNECTED"
                    ui.draw_offer_status = None 
                    ui.rematch_status = "IDLE"
            elif msg_type == "CHAT":
                audio_manager.play_sfx('notify')
                ui.chat_messages.append(f"{msg.get('sender')}: {msg.get('text')}")
                
            elif msg_type == "MOVE":
                uci_move = msg.get("move")
                move = chess.Move.from_uci(uci_move)
                if move in ui.board.legal_moves:
                    ui.board.push(move)
                    ui.sync_board_state() 
                    
                    if ui.board.is_checkmate(): audio_manager.play_sfx('checkmate')
                    elif ui.board.is_check(): audio_manager.play_sfx('check')
                    else: audio_manager.play_sfx('move')
                    
            elif msg_type == "OPPONENT_SURRENDERED":
                audio_manager.play_sfx('win')
                ui.end_state = "WIN"
                ui.draw_offer_status = None

            elif msg_type == "OPPONENT_TIMEOUT":
                audio_manager.play_sfx('win')
                ui.end_state = "WIN"
                ui.draw_offer_status = None
                ui.chat_messages.append("Hệ thống: Đối thủ đã hết thời gian!")

            elif msg_type == "GAME_OVER":
                res = msg.get("result")
                if (res == "1-0" and ui.color == "WHITE") or (res == "0-1" and ui.color == "BLACK"):
                    ui.end_state = "WIN"
                    audio_manager.play_sfx('win')
                elif res == "1/2-1/2":
                    ui.end_state = "DRAW"
                    audio_manager.play_sfx('draw')
                else:
                    ui.end_state = "LOSS"
                    audio_manager.play_sfx('lose')
                ui.draw_offer_status = None
            
            elif msg_type == "REMATCH_REQUESTED":
                audio_manager.play_sfx('notify')
                ui.rematch_status = "RECEIVED"
                
            elif msg_type == "REMATCH_ACCEPTED":
                ui.reset_board() 

            elif msg_type == "REMATCH_DECLINED":
                audio_manager.play_sfx('notify')
                ui.chat_messages.append("Hệ thống: Đối thủ đã từ chối đấu lại!")
                ui.rematch_status = "IDLE"

            elif msg_type == "OPPONENT_DISCONNECTED":
                audio_manager.play_sfx('notify')
                ui.chat_messages.append("Hệ thống: Đối thủ đã rời phòng!")
                if not ui.end_state:
                    ui.end_state = "WIN" 
                    audio_manager.play_sfx('win')
                ui.rematch_status = "OPPONENT_LEFT"
        
            elif msg_type == "DRAW_OFFERED":
                audio_manager.play_sfx('notify')
                ui.draw_offer_status = "RECEIVED"
                ui.draw_timer_start = time.time() 

            elif msg_type == "DRAW_DECLINED":
                audio_manager.play_sfx('notify')
                ui.draw_offer_status = None 
                ui.chat_messages.append("Hệ thống: Đối thủ đã từ chối cầu hòa!")

        # TIMEOUT CHO CẦU HÒA
        if ui.draw_offer_status in ["WAITING", "RECEIVED"]:
            if time.time() - ui.draw_timer_start > 15:
                if ui.draw_offer_status == "WAITING":
                    ui.chat_messages.append("Hệ thống: Đối thủ không phản hồi, đã hủy yêu cầu!")
                elif ui.draw_offer_status == "RECEIVED":
                    net.send({"type": "DRAW_RESPONSE", "accepted": False}) 
                ui.draw_offer_status = None

        # TIMEOUT CHO REMATCH 
        if ui.rematch_status == "WAITING":
            if time.time() - getattr(ui, 'rematch_timer_start', time.time()) > 15:
                ui.rematch_status = "IDLE"
                ui.chat_messages.append("Hệ thống: Hết thời gian chờ phản hồi đấu lại!")
                net.send({"type": "DECLINE_REMATCH"})

        # ĐỒNG HỒ ĐẾM NGƯỢC
        if not ui.end_state and ui.rematch_status == "IDLE" and not ui.draw_offer_status:
            current_time = time.time()
            dt = current_time - ui.last_tick
            ui.last_tick = current_time
            
            is_my_turn = (ui.board.turn == chess.WHITE and ui.color == "WHITE") or \
                         (ui.board.turn == chess.BLACK and ui.color == "BLACK")
            
            if is_my_turn:
                ui.my_time -= dt
                if ui.my_time <= 0 and not ui.timeout_sent:
                    ui.my_time = 0
                    ui.end_state = "LOSS"
                    ui.draw_offer_status = None
                    ui.chat_messages.append("Hệ thống: Bạn đã hết thời gian!")
                    net.send({"type": "TIMEOUT"}) 
                    ui.timeout_sent = True
                    audio_manager.play_sfx('lose')
            else:
                ui.opp_time -= dt
                if ui.opp_time <= 0:
                    ui.opp_time = 0
        else:
            ui.last_tick = time.time() 
        
        ui.draw()

        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            elif e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                ui.surface = screen
                ui.update_layout()
                
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                mouse_pos = e.pos

                # ƯU TIÊN 0: BẢNG PHONG CẤP
                if getattr(ui, 'promotion_pending', None):
                    if ui.board_rect.collidepoint(mouse_pos):
                        for key, rect in ui.promo_rects.items():
                            if rect.collidepoint(mouse_pos):
                                audio_manager.play_sfx('click')
                                net.send({"type": "MOVE", "move": ui.promotion_pending + key})
                                ui.promotion_pending = None
                                break
                        if ui.promotion_pending and not any(r.collidepoint(mouse_pos) for r in ui.promo_rects.values()):
                            ui.promotion_pending = None
                            ui.selected_square = None
                            ui.possible_moves = []
                        continue 

                # ƯU TIÊN 1: BẢNG CẦU HÒA
                if ui.draw_offer_status:
                    if ui.draw_offer_status == "RECEIVED":
                        if ui.end_btn1_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            net.send({"type": "DRAW_RESPONSE", "accepted": True})
                            ui.draw_offer_status = None
                        elif ui.end_btn2_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            net.send({"type": "DRAW_RESPONSE", "accepted": False})
                            ui.draw_offer_status = None
                    elif ui.draw_offer_status == "DECLINED":
                        if ui.center_btn_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            ui.draw_offer_status = None
                    continue 

                # ƯU TIÊN 2: GAME ĐÃ KẾT THÚC
                if ui.end_state:
                    if ui.end_state == "SERVER_DISCONNECTED":
                        if ui.center_btn_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            return "BACK_TO_MENU"

                    elif ui.rematch_status == "IDLE":
                        if ui.end_btn1_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            ui.rematch_status = "WAITING"
                            ui.rematch_timer_start = time.time() 
                            net.send({"type": "REQUEST_REMATCH"})
                        elif ui.end_btn2_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            net.send({"type": "LEAVE_ROOM"})
                            return "BACK_TO_MENU"
                            
                    elif ui.rematch_status == "WAITING":
                        pass 
                            
                    elif ui.rematch_status == "OPPONENT_LEFT":
                        if ui.center_btn_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            net.send({"type": "LEAVE_ROOM"})
                            return "BACK_TO_MENU"

                    elif ui.rematch_status == "RECEIVED":
                        if ui.end_btn1_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            net.send({"type": "ACCEPT_REMATCH"})
                        elif ui.end_btn2_rect.collidepoint(mouse_pos): 
                            audio_manager.play_sfx('click')
                            net.send({"type": "DECLINE_REMATCH"})
                            ui.rematch_status = "IDLE" 

                    continue 

                # ƯU TIÊN 3: GAME ĐANG ĐÁNH BÌNH THƯỜNG
                ui.input_active = ui.chat_input_rect.collidepoint(mouse_pos)

                if ui.surrender_rect.collidepoint(mouse_pos):
                    audio_manager.play_sfx('click')
                    ui.end_state = "LOSS" 
                    audio_manager.play_sfx('lose')
                    ui.draw_offer_status = None
                    net.send({"type": "SURRENDER"})
                    
                if ui.draw_rect.collidepoint(mouse_pos):
                    audio_manager.play_sfx('click')
                    net.send({"type": "OFFER_DRAW"})
                    ui.draw_offer_status = "WAITING"
                    ui.draw_timer_start = time.time() 

                # XỬ LÝ CLICK BÀN CỜ (CÓ BỘ LỌC CHỐNG CRASH)
                clicked_square = ui.get_square_from_mouse(mouse_pos)
                if clicked_square is not None:
                    my_chess_color = chess.WHITE if ui.color == "WHITE" else chess.BLACK
                    
                    if ui.selected_square == clicked_square:
                        ui.selected_square = None
                        ui.possible_moves = []
                    
                    elif ui.board.piece_at(clicked_square) and ui.board.piece_at(clicked_square).color == my_chess_color:
                        ui.selected_square = clicked_square
                        ui.possible_moves = [m for m in ui.board.legal_moves if m.from_square == clicked_square]
                        
                        logical_c = chess.square_file(clicked_square)
                        logical_r = 7 - chess.square_rank(clicked_square)
                        ui.dragging = True
                        ui.drag_piece = ui.board_state[logical_r][logical_c]
                        ui.drag_start_pos = (logical_r, logical_c)
                    
                    elif ui.selected_square is not None:
                        if ui.drag_start_pos is not None:
                            logical_c = chess.square_file(clicked_square)
                            logical_r = 7 - chess.square_rank(clicked_square)
                            
                            uci_str = ui.pos_to_uci(ui.drag_start_pos[0], ui.drag_start_pos[1]) + ui.pos_to_uci(logical_r, logical_c)
                            
                            try: test_promo = chess.Move.from_uci(uci_str + 'q')
                            except: test_promo = None
                            
                            try: test_normal = chess.Move.from_uci(uci_str)
                            except: test_normal = None

                            if ui.drag_piece.endswith('P') and (logical_r == 0 or logical_r == 7) and (test_promo in ui.board.legal_moves): 
                                ui.promotion_pending = uci_str
                            elif test_normal in ui.board.legal_moves: 
                                net.send({"type": "MOVE", "move": uci_str})
                        
                        ui.selected_square = None
                        ui.possible_moves = []
                        ui.dragging = False
                        ui.drag_piece = ''
                        ui.drag_start_pos = None

            elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                if ui.dragging:
                    mouse_pos = e.pos
                    if ui.board_rect.collidepoint(mouse_pos):
                        screen_c = (mouse_pos[0] - ui.board_rect.x) // ui.sq_size
                        screen_r = (mouse_pos[1] - ui.board_rect.y) // ui.sq_size
                        target_r, target_c = ui.get_board_pos(screen_r, screen_c)
                        
                        if (target_r, target_c) != ui.drag_start_pos:
                            uci_str = ui.pos_to_uci(ui.drag_start_pos[0], ui.drag_start_pos[1]) + ui.pos_to_uci(target_r, target_c)
                            
                            try: test_promo = chess.Move.from_uci(uci_str + 'q')
                            except: test_promo = None
                            
                            try: test_normal = chess.Move.from_uci(uci_str)
                            except: test_normal = None

                            if ui.drag_piece.endswith('P') and (target_r == 0 or target_r == 7) and (test_promo in ui.board.legal_moves): 
                                ui.promotion_pending = uci_str
                            elif test_normal in ui.board.legal_moves: 
                                net.send({"type": "MOVE", "move": uci_str})
                                
                        ui.selected_square = None
                        ui.possible_moves = []
                        ui.dragging = False
                        ui.drag_piece = ''
                        ui.drag_start_pos = None
                    else:
                        ui.dragging = False
                else:
                    ui.dragging = False
                    ui.selected_square = None
                    ui.possible_moves = []

            elif e.type == pygame.KEYDOWN:
                if ui.input_active:
                    if e.key == pygame.K_RETURN:
                        if ui.chat_input.strip() != "":
                            audio_manager.play_sfx('click')
                            net.send({"type": "CHAT", "text": ui.chat_input})
                            ui.chat_messages.append(f"{ui.player_name}: {ui.chat_input}")
                            ui.chat_input = "" 
                    elif e.key == pygame.K_BACKSPACE: 
                        ui.chat_input = ui.chat_input[:-1]
                        audio_manager.play_sfx('click')
                    else:
                        if len(ui.chat_input) < 40: 
                            ui.chat_input += e.unicode
                            audio_manager.play_sfx('click')
                else:
                    if e.key == pygame.K_ESCAPE: 
                        audio_manager.play_sfx('click')
                        return "BACK_TO_MENU"

        pygame.display.flip()
        clock.tick(60)