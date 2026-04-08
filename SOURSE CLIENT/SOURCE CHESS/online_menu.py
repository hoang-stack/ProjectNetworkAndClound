import pygame
import sys
import time
import json
import audio_manager

class OnlineMenuUI:
    def __init__(self, surface):
        self.surface = surface
        
        # CÁC TRẠNG THÁI CỦA MENU NÀY: "MAIN", "ROOM", "SEARCHING"
        self.state = "MAIN" 
        
        self.room_id_text = ""
        self.input_active = False
        self.search_angle = 0
        self.created_room_code = "" # Biến để hiển thị mã phòng lên màn hình

        self.update_layout()

    def load_scaled_image(self, path, size):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except:
            s = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(s, (100, 100, 100), s.get_rect(), border_radius=5)
            return s

    def update_layout(self):
        w, h = self.surface.get_size()
        cx, cy = w // 2, h // 2

        try:
            bg = pygame.image.load("assets/menu_bg.png").convert()
            self.bg_img = pygame.transform.smoothscale(bg, (w, h))
        except:
            self.bg_img = pygame.Surface((w, h))
            self.bg_img.fill((40, 40, 60))
        
        self.dark_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        self.dark_overlay.fill((0, 0, 0, 200)) 

        self.btn_w = w // 4
        self.btn_h = int(self.btn_w / 4.2)
        btn_size = (self.btn_w, self.btn_h)
        self.gap = h // 20
        self.back_w = w // 8
        self.back_h = int(self.back_w / 4.2)
        self.back_rect = pygame.Rect(20, 20, self.back_w, self.back_h)
        
        self.pvp_rect = pygame.Rect(cx - self.btn_w // 2, cy - self.btn_h - self.gap//2, self.btn_w, self.btn_h)
        self.room_rect = pygame.Rect(cx - self.btn_w // 2, cy + self.gap//2, self.btn_w, self.btn_h)
        
        self.create_rect = pygame.Rect(cx - self.btn_w // 2, cy - self.btn_h - self.gap, self.btn_w, self.btn_h)
        self.input_rect = pygame.Rect(cx - self.btn_w // 2, cy, self.btn_w, self.btn_h)
        self.join_rect = pygame.Rect(cx - self.btn_w // 2, self.input_rect.bottom + self.gap, self.btn_w, self.btn_h)
        
        self.loading_size = (h // 6, h // 6)
        self.img_loading = self.load_scaled_image("assets/loading.png", self.loading_size)
        
        self.cancel_rect = pygame.Rect(cx - self.btn_w // 4, cy + self.loading_size[1] // 2 + 30, self.btn_w // 2, self.btn_h)

        self.img_pvp = self.load_scaled_image("assets/btn_pvp.png", btn_size)
        self.img_pvp_h = self.load_scaled_image("assets/btn_pvp_hover.png", btn_size)
        self.img_room = self.load_scaled_image("assets/btn_room.png", btn_size)
        self.img_room_h = self.load_scaled_image("assets/btn_room_hover.png", btn_size)
        self.img_create = self.load_scaled_image("assets/btn_create.png", btn_size)
        self.img_create_h = self.load_scaled_image("assets/btn_create_hover.png", btn_size)
        self.img_join = self.load_scaled_image("assets/btn_join.png", btn_size)
        self.img_join_h = self.load_scaled_image("assets/btn_join_hover.png", btn_size)
        self.img_back = self.load_scaled_image("assets/btn_back.png", (self.back_w, self.back_h))
        self.img_back_h = self.load_scaled_image("assets/btn_back_hover.png", (self.back_w, self.back_h))
        cancel_size = (self.btn_w // 2, self.btn_h)
        self.img_cancel = self.load_scaled_image("assets/btn_cancel.png", cancel_size)
        self.img_cancel_h = self.load_scaled_image("assets/btn_cancel_hover.png", cancel_size)

        font_size = max(20, h // 30)
        font_size_small = max(14, h // 55)
        try: 
            self.font = pygame.font.SysFont("segoeui", font_size, bold=True)
            self.font_small = pygame.font.SysFont("segoeui", font_size_small, bold=False)
        except: 
            self.font = pygame.font.SysFont("tahoma", font_size, bold=True)
            self.font_small = pygame.font.SysFont("tahoma", font_size_small, bold=False)

    def draw(self):
            self.surface.blit(self.bg_img, (0, 0))
            self.surface.blit(self.dark_overlay, (0, 0))
            
            mouse_pos = pygame.mouse.get_pos()
            cx, cy = self.surface.get_width() // 2, self.surface.get_height() // 2

            def draw_button(rect, img_norm, img_hover):
                self.surface.blit(img_hover if rect.collidepoint(mouse_pos) else img_norm, rect)

            if self.state != "SEARCHING":
                draw_button(self.back_rect, self.img_back, self.img_back_h)

            if self.state == "MAIN":
                draw_button(self.pvp_rect, self.img_pvp, self.img_pvp_h)
                draw_button(self.room_rect, self.img_room, self.img_room_h)

            elif self.state == "ROOM":
                draw_button(self.create_rect, self.img_create, self.img_create_h)
                or_txt = self.font_small.render("OR", True, (150, 150, 150))
                or_cy = self.create_rect.bottom + self.gap // 2
                or_rect = or_txt.get_rect(center=(cx, or_cy))
                self.surface.blit(or_txt, or_rect)
                
                pygame.draw.line(self.surface, (150, 150, 150), 
                                (cx - self.btn_w//2, or_cy), (or_rect.left - 15, or_cy), 2)
                pygame.draw.line(self.surface, (150, 150, 150), 
                                (or_rect.right + 15, or_cy), (cx + self.btn_w//2, or_cy), 2)
                draw_button(self.join_rect, self.img_join, self.img_join_h)
                color = (0, 255, 255) if self.input_active else (255, 255, 255)
                pygame.draw.rect(self.surface, color, self.input_rect, 3, border_radius=8)
                display_txt = self.room_id_text
                if self.input_active and (pygame.time.get_ticks() // 500) % 2: display_txt += "|"
                if display_txt == "" and not self.input_active:
                    txt_surf = self.font.render("Input Room ID to join...", True, (150, 150, 150))
                else:
                    txt_surf = self.font.render(display_txt, True, (255, 255, 255))
                self.surface.blit(txt_surf, (self.input_rect.x + 15, self.input_rect.y + (self.btn_h - txt_surf.get_height())//2))

            elif self.state == "SEARCHING":
                if self.created_room_code != "":
                    text_show = f"Room Code: {self.created_room_code} - Waiting..."
                else:
                    text_show = "Finding opponent..."
                    
                txt_surf = self.font.render(text_show, True, (0, 255, 255))
                self.surface.blit(txt_surf, (cx - txt_surf.get_width()//2, cy - self.loading_size[1] // 2 - 50))

                self.search_angle = (self.search_angle - 5) % 360 
                rotated = pygame.transform.rotate(self.img_loading, -self.search_angle)
                
                rect = rotated.get_rect(center=(cx, cy))
                self.surface.blit(rotated, rect)
                draw_button(self.cancel_rect, self.img_cancel, self.img_cancel_h)

def run(screen, net, player_name):
    ui = OnlineMenuUI(screen)
    clock = pygame.time.Clock()

    if player_name.strip() != "":
        try: net.send({"type": "SET_NAME", "name": player_name})
        except: pass

    show_dc_toast = False
    dc_toast_start = 0

    show_error = False
    error_time = 0
    error_msg = ""
    font_err = pygame.font.SysFont("segoeui", 25, bold=True)
    try:
        img_panel_dc = pygame.image.load("assets/panel_disconnect.png").convert_alpha()
        img_panel_dc = pygame.transform.smoothscale(img_panel_dc, (screen.get_width()//3, screen.get_height()//3))
    except:
        pass 
    
    while True:
        try:
            messages = net.get_messages()
        except:
            messages = [] 
            if ui.state == "SEARCHING":
                ui.state = "MAIN"
                show_dc_toast = True
                dc_toast_start = time.time()
                audio_manager.play_sfx('notify')

        for msg in messages:
            msg_type = msg.get("type")
            
            if msg_type == "WELCOME":
                if player_name.strip() == "":
                    player_name = "Player_" + msg.get("id") 
                    net.send({"type": "SET_NAME", "name": player_name})

            if msg_type == "MATCHED":
                audio_manager.play_sfx('notify')
                print(f"[UI] Đã tìm thấy đối thủ: {msg.get('opponent')}! Bạn cầm cờ {msg.get('color')}")
                return {
                    "action": "START_GAME", 
                    "color": msg.get("color"), 
                    "opponent": msg.get("opponent"),
                    "my_name": player_name  
                }
                
            elif msg_type == "ROOM_CREATED":
                audio_manager.play_sfx('notify') 
                print(f"[UI] Phòng đã tạo thành công! Mã phòng: {msg.get('room_code')}")
                ui.created_room_code = msg.get("room_code")
                
            elif msg_type == "ERROR":
                audio_manager.play_sfx('notify') 
                print(f"[!] Lỗi: {msg.get('msg')}")
                ui.state = "ROOM"
                show_error = True
                error_time = time.time()
                error_msg = msg.get('msg')

        ui.draw()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            elif e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                ui.surface = screen
                ui.update_layout()
                
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    audio_manager.play_sfx('click')
                    if ui.state == "ROOM": ui.state = "MAIN"
                    elif ui.state == "MAIN": return "BACK"
                
                elif ui.state == "ROOM" and ui.input_active:
                    if e.key == pygame.K_BACKSPACE: 
                        ui.room_id_text = ui.room_id_text[:-1]
                        audio_manager.play_sfx('click')
                    elif e.key == pygame.K_RETURN: 
                        ui.input_active = False
                        audio_manager.play_sfx('click')
                    else:
                        if len(ui.room_id_text) < 5 and e.unicode.isalnum():
                            ui.room_id_text += e.unicode.upper()
                            audio_manager.play_sfx('click')
                            
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if show_dc_toast:
                    continue
                
                pos = e.pos
                
                if ui.state == "MAIN":
                    if ui.back_rect.collidepoint(pos): 
                        audio_manager.play_sfx('click')
                        return "BACK"
                    
                    elif ui.pvp_rect.collidepoint(pos):
                        audio_manager.play_sfx('click')
                        if not net.check_connection():
                            show_dc_toast = True
                            dc_toast_start = time.time()
                            audio_manager.play_sfx('notify')
                        else:
                            ui.state = "SEARCHING"
                            net.send({"type": "FIND_PVP"})
                        
                    elif ui.room_rect.collidepoint(pos): 
                        audio_manager.play_sfx('click')
                        ui.state = "ROOM"
                
                elif ui.state == "ROOM":
                    if ui.back_rect.collidepoint(pos): 
                        audio_manager.play_sfx('click')
                        ui.state = "MAIN"
                        
                    if ui.input_rect.collidepoint(pos): 
                        audio_manager.play_sfx('click') 
                        ui.input_active = True
                    else: 
                        ui.input_active = False
                    
                    if ui.create_rect.collidepoint(pos):
                        audio_manager.play_sfx('click') 
                        if not net.check_connection():
                            show_dc_toast = True
                            dc_toast_start = time.time()
                            audio_manager.play_sfx('notify')
                        else:
                            net.send({"type": "CREATE_ROOM"})
                            ui.state = "SEARCHING" 
                        
                    elif ui.join_rect.collidepoint(pos):
                        audio_manager.play_sfx('click') 
                        if len(ui.room_id_text) > 0:
                            if not net.check_connection():
                                show_dc_toast = True
                                dc_toast_start = time.time()
                                audio_manager.play_sfx('notify') 
                            else:
                                net.send({"type": "JOIN_ROOM", "room_code": ui.room_id_text})
                                ui.state = "SEARCHING"
                
                elif ui.state == "SEARCHING":
                    if ui.cancel_rect.collidepoint(pos): 
                        audio_manager.play_sfx('click') 
                        ui.state = "MAIN"
                        try: net.send({"type": "CANCEL_PVP"})
                        except: pass
                        
        # --- VẼ HIỆU ỨNG MẤT KẾT NỐI (ĐÈ LÊN TẤT CẢ) ---
        if show_dc_toast:
            elapsed = time.time() - dc_toast_start
            if elapsed < 1.5:
                overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150)) 
                screen.blit(overlay, (0, 0))
                
                alpha = 255
                if elapsed > 1.0: 
                    alpha = int(255 * (1.5 - elapsed) / 0.5)
                
                if 'img_panel_dc' in locals():
                    panel_copy = img_panel_dc.copy()
                    panel_copy.set_alpha(alpha)
                    screen.blit(panel_copy, panel_copy.get_rect(center=(screen.get_width()//2, screen.get_height()//2)))
                
                pygame.event.clear(pygame.MOUSEBUTTONDOWN)
            else:
                show_dc_toast = False
        if show_error:
            if time.time() - error_time < 1.0:
                # Vẽ chữ màu đỏ (255, 50, 50)
                txt_surf = font_err.render(error_msg, True, (255, 50, 50))
                txt_rect = txt_surf.get_rect(center=(screen.get_width()//2, screen.get_height()//2 - 100))
                screen.blit(txt_surf, txt_rect)
            else:
                show_error = False
        pygame.display.flip()
        clock.tick(60)