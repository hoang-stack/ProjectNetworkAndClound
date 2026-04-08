import pygame
import ctypes
import sys,os
import time      
import network   
from online_menu import OnlineMenuUI
import audio_manager


if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

pygame.init()
audio_manager.init_audio()
audio_manager.play_bgm("menu")

# --- CHỐNG MỜ MÀN HÌNH WINDOWS ---
try: ctypes.windll.user32.SetProcessDPIAware()
except: pass

ASPECT_RATIO = 16 / 9 
INITIAL_W = 1280
INITIAL_H = int(INITIAL_W / ASPECT_RATIO) 

screen = pygame.display.set_mode((INITIAL_W, INITIAL_H), pygame.RESIZABLE)
pygame.display.set_caption("Chess36 - From @36_is_a_number_that_breaks_all_stereotypes.36")
try:
    icon_img = pygame.image.load("assets/icon.png") 
    pygame.display.set_icon(icon_img)
except Exception as e:
    print("Không load được icon:", e)
# =========================================================
# === CLASS QUẢN LÝ GIAO DIỆN MENU ===
# =========================================================
class MenuUI:
    def __init__(self, surface):
        self.surface = surface
        self.player_name = ""
        self.input_active = False
        
        # Biến cho ô nhập IP
        self.ip_text = ""
        self.ip_active = False
        
        self.update_layout()

    def load_scaled_image(self, path, size):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        except:
            surface = pygame.Surface(size, pygame.SRCALPHA)
            surface.fill((100, 100, 100))
            return surface

    def update_layout(self):
        w, h = self.surface.get_size()
        cx, cy = w // 2, h // 2

        try:
            bg = pygame.image.load("assets/menu_bg.png").convert()
            self.bg_img = pygame.transform.smoothscale(bg, (w, h))
        except:
            self.bg_img = pygame.Surface((w, h))
            self.bg_img.fill((30, 30, 30))

        self.btn_w = w // 4
        self.btn_h = h // 10
        btn_size = (self.btn_w, self.btn_h)

        self.inp_w = w // 3
        self.inp_h = h // 10
        self.gap = h // 32

        font_size = max(20, h // 25) 
        try: self.font = pygame.font.SysFont("segoeui", font_size, bold=True)
        except: self.font = pygame.font.SysFont("tahoma", font_size, bold=True)

        self.input_rect = pygame.Rect(cx - self.inp_w // 2, cy - self.inp_h, self.inp_w, self.inp_h)
        self.online_rect = pygame.Rect(cx - self.btn_w // 2, self.input_rect.bottom + self.gap, self.btn_w, self.btn_h)
        self.single_rect = pygame.Rect(cx - self.btn_w // 2, self.online_rect.bottom + self.gap, self.btn_w, self.btn_h)
        self.quit_rect = pygame.Rect(cx - self.btn_w // 2, self.single_rect.bottom + self.gap, self.btn_w, self.btn_h)

        self.img_online = self.load_scaled_image("assets/btn_online.png", btn_size)
        self.img_online_h = self.load_scaled_image("assets/btn_online_hover.png", btn_size)
        self.img_single = self.load_scaled_image("assets/btn_single.png", btn_size)
        self.img_single_h = self.load_scaled_image("assets/btn_single_hover.png", btn_size)
        self.img_quit = self.load_scaled_image("assets/btn_quit.png", btn_size)
        self.img_quit_h = self.load_scaled_image("assets/btn_quit_hover.png", btn_size)

        # Nút âm thanh (Góc phải trên)
        sound_size = int(h // 12)
        self.sound_rect = pygame.Rect(w - sound_size - 20, 20, sound_size, sound_size)
    
        self.img_sound_on = self.load_scaled_image("assets/sound_on.png", (sound_size, sound_size))
        self.img_sound_hover = self.load_scaled_image("assets/sound_hover.png", (sound_size, sound_size))
        self.img_sound_off = self.load_scaled_image("assets/sound_off.png", (sound_size, sound_size))

        # Tính toán layout cho ô nhập IP (Góc phải dưới)
        self.ip_w = max(180, int(w * 0.15))
        self.ip_h = max(35, int(h * 0.05))
        self.ip_rect = pygame.Rect(w - self.ip_w - 20, h - self.ip_h - 20, self.ip_w, self.ip_h)

        ip_font_size = max(16, self.ip_h - 15)
        try: 
            self.ip_font = pygame.font.SysFont("consolas", ip_font_size, bold=True)
        except: 
            self.ip_font = pygame.font.SysFont("segoeui", ip_font_size, bold=True)
    def draw(self):
        self.surface.blit(self.bg_img, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. Vẽ ô nhập Tên
        border_color = (0, 255, 255) if self.input_active else (200, 200, 200)
        s = pygame.Surface((self.input_rect.width, self.input_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150)) 
        self.surface.blit(s, (self.input_rect.x, self.input_rect.y))
        pygame.draw.rect(self.surface, border_color, self.input_rect, 3, border_radius=8)

        if self.player_name == "" and not self.input_active:
            txt_surf = self.font.render("Nhập tên...", True, (150, 150, 150))
        else:
            txt_surf = self.font.render(self.player_name, True, (255, 255, 255))
        
        txt_x = self.input_rect.x + (self.inp_w - txt_surf.get_width()) // 2
        txt_y = self.input_rect.y + (self.inp_h - txt_surf.get_height()) // 2
        self.surface.blit(txt_surf, (txt_x, txt_y))

        # 2. Vẽ các nút
        def draw_button(rect, img_norm, img_hover):
            self.surface.blit(img_hover if rect.collidepoint(mouse_pos) else img_norm, rect)

        draw_button(self.online_rect, self.img_online, self.img_online_h)
        draw_button(self.single_rect, self.img_single, self.img_single_h)
        draw_button(self.quit_rect, self.img_quit, self.img_quit_h)

        # 3. Vẽ nút âm thanh
        if audio_manager.is_muted:
            self.surface.blit(self.img_sound_off, self.sound_rect)
        else:
            if self.sound_rect.collidepoint(mouse_pos):
                self.surface.blit(self.img_sound_hover, self.sound_rect)
            else:
                self.surface.blit(self.img_sound_on, self.sound_rect) 

        # Vẽ ô nhập IP
        ip_label = self.ip_font.render("Server IP:", True, (160,160,160))
        label_y = self.ip_rect.y - ip_label.get_height() - 5 
        self.surface.blit(ip_label, (self.ip_rect.x, label_y))

        ip_border = (0, 255, 255) if self.ip_active else (150, 150, 150)
        pygame.draw.rect(self.surface, (30, 30, 30), self.ip_rect, border_radius=4)
        pygame.draw.rect(self.surface, ip_border, self.ip_rect, 2, border_radius=4)

        if self.ip_text == "" and not self.ip_active:
            ip_surf = self.ip_font.render("127.0.0.1", True, (100, 100, 100))
        else:
            ip_surf = self.ip_font.render(self.ip_text, True, (255, 255, 255))
        
        self.surface.blit(ip_surf, (self.ip_rect.x + 8, self.ip_rect.y + (self.ip_rect.height - ip_surf.get_height())//2))


# =========================================================
# === VÒNG LẶP CHÍNH ===
# =========================================================
def main():
    global screen
    menu = MenuUI(screen)
    is_fullscreen = False
    
    show_dc_toast = False
    dc_toast_start = 0

    try:
        img_panel_dc = pygame.image.load("assets/panel_disconnect.png").convert_alpha()
        img_panel_dc = pygame.transform.smoothscale(img_panel_dc, (screen.get_width()//3, int(screen.get_height() * 0.4)))
    except:
        pass 
    
    while True:
        menu.draw()

        # --- VẼ HIỆU ỨNG MẤT KẾT NỐI VÀ LÀM MỜ ---
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
            else:
                show_dc_toast = False

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            elif e.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
                menu.surface = screen
                menu.update_layout()
                
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if show_dc_toast:
                    continue

                mouse_pos = e.pos

                if menu.sound_rect.collidepoint(mouse_pos):
                    audio_manager.toggle_mute()
                    continue

                # <--- CẬP NHẬT: QUẢN LÝ CLICK CHUỘT THÔNG MINH HƠN --->
                if menu.input_rect.collidepoint(mouse_pos):
                    menu.input_active = True
                    menu.ip_active = False # Tắt ô IP
                    audio_manager.play_sfx('click') 
                elif menu.ip_rect.collidepoint(mouse_pos):
                    menu.ip_active = True
                    menu.input_active = False # Tắt ô Tên
                    audio_manager.play_sfx('click')
                else:
                    menu.input_active = False
                    menu.ip_active = False
                    
                    # 1. BẤM NÚT ONLINE
                    if menu.online_rect.collidepoint(mouse_pos):
                        audio_manager.play_sfx('click') 
                        print(f"-> Đang kết nối Server...")
                        net = network.Network()
                        
                        # ---> LẤY IP TỪ Ô NHẬP HOẶC DÙNG MẶC ĐỊNH <---
                        final_ip = menu.ip_text.strip() if menu.ip_text.strip() != "" else "127.0.0.1"
                        
                        if net.connect(final_ip): 
                            import online_menu
                            result = online_menu.run(screen, net, menu.player_name) 
                            
                            if type(result) == dict and result.get("action") == "START_GAME":
                                import game_play
                                audio_manager.play_bgm("match")
                                game_play.run(screen, result['my_name'], result['opponent'], net, result['color'])
                                audio_manager.play_bgm("menu")

                            menu.surface = screen
                            menu.update_layout()
                            
                        else:
                            print(f"[!] LỖI: Server {final_ip} chưa bật hoặc rớt mạng!")
                            audio_manager.play_sfx('notify')
                            show_dc_toast = True
                            dc_toast_start = time.time()

                    # 2. BẤM NÚT SINGLE PLAY
                    elif menu.single_rect.collidepoint(mouse_pos):
                        audio_manager.play_sfx('click') 
                        print("Click Play Single")
                        import single_play
                        
                        audio_manager.play_bgm("match")
                        single_play.run(screen)
                        audio_manager.play_bgm("menu")

                        screen = pygame.display.get_surface() 
                        menu.surface = screen
                        menu.update_layout()
                    
                    # 3. BẤM QUIT
                    elif menu.quit_rect.collidepoint(mouse_pos):
                        audio_manager.play_sfx('click') 
                        time.sleep(0.1)
                        pygame.quit(); sys.exit()

            # Nhập từ bàn phím
            elif e.type == pygame.KEYDOWN:
                if menu.input_active:
                    if e.key == pygame.K_BACKSPACE:
                        menu.player_name = menu.player_name[:-1]
                        audio_manager.play_sfx('click')
                    elif e.key == pygame.K_RETURN:
                        menu.input_active = False
                        audio_manager.play_sfx('click')
                elif menu.ip_active:
                    if e.key == pygame.K_BACKSPACE:
                        menu.ip_text = menu.ip_text[:-1]
                        audio_manager.play_sfx('click')
                    elif e.key == pygame.K_RETURN:
                        menu.ip_active = False
                        audio_manager.play_sfx('click')

            elif e.type == pygame.TEXTINPUT:
                if menu.input_active:
                    if len(menu.player_name) < 15:
                        menu.player_name += e.text 
                        audio_manager.play_sfx('click')
                elif menu.ip_active:
                    if len(menu.ip_text) < 15 and (e.text.isdigit() or e.text == '.'):
                        menu.ip_text += e.text
                        audio_manager.play_sfx('click')

        pygame.display.flip()

if __name__ == "__main__":
    main()