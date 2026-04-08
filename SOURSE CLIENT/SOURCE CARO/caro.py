import pygame
import math
import threading
import socket
import json
import queue
import time
import sys,os
import ctypes
import audio_caro
from audio_caro import play_sfx

if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

WHITE = (255, 255, 255)
BLUE = (0, 110, 255)
DARK_BLUE = (20, 80, 200)
ORANGE = (210, 120, 50)
LIGHT_BLUE = (0, 180, 255)

ngang_game = 533
doc_game = 533

game_state = "MENU" 

class GiaoDien:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        pygame.font.init()
        # Giảm cỡ chữ đồng loạt, dùng font tahoma để không lỗi tiếng Việt
        self.font_large = pygame.font.SysFont("tahoma", 28, bold=True) 
        self.font_small = pygame.font.SysFont("tahoma", 14, bold=True)
        self.font_banner = pygame.font.SysFont("tahoma", 18, bold=True)

    def draw_rounded_button(self, text, y_pos): 
        # Thu nhỏ nút bấm Menu chính nhường chỗ cho ô IP
        rect_width, rect_height = 300, 45 
        
        rect_x = (self.width - rect_width) // 2
        button_rect = pygame.Rect(rect_x, y_pos, rect_width, rect_height)
        pygame.draw.rect(self.screen, BLUE, button_rect, border_radius=20) 
        text_surf = self.font_large.render(text, True, WHITE)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)
        return button_rect

    def draw_banner(self):
        center_x = self.width // 2
        pygame.draw.rect(self.screen, DARK_BLUE, (center_x - 110, 55, 220, 35))
        banner_text = self.font_banner.render("CARO", True, WHITE)
        self.screen.blit(banner_text, (center_x - 30, 62)) 
        points = [
            (center_x - 90, 90), (center_x + 90, 90),
            (center_x + 90, 210), (center_x, 240), (center_x - 90, 210)
        ]
        pygame.draw.polygon(self.screen, BLUE, points)
        
        xo_font = pygame.font.SysFont("tahoma", 50, bold=True)
        self.screen.blit(xo_font.render("X O", True, WHITE), (center_x - 45, 120))
        self.screen.blit(xo_font.render("O X", True, WHITE), (center_x - 45, 170))

    def draw_all(self, ip_text, is_ip_active):
        self.screen.fill(WHITE)
        self.draw_banner()
        
        # 1. Vẽ ô nhập IP
        box_width, box_height = 300, 40
        rect_x = (self.width - box_width) // 2
        ip_rect = pygame.Rect(rect_x, 275, box_width, box_height)
        
        color = BLUE if is_ip_active else (150, 150, 150)
        pygame.draw.rect(self.screen, (245, 245, 245), ip_rect, border_radius=10)
        pygame.draw.rect(self.screen, color, ip_rect, width=2, border_radius=10)
        
        display_text = ip_text if ip_text else "127.0.0.1 (Mặc định)"
        text_color = (0, 0, 0) if ip_text else (150, 150, 150)
        
        txt_surface = self.font_banner.render(display_text, True, text_color)
        self.screen.blit(txt_surface, (ip_rect.x + 10, ip_rect.y + 7))
        
        label = self.font_small.render("Server IP:", True, (100, 100, 100))
        self.screen.blit(label, (ip_rect.x, ip_rect.y - 18))

        # 2. Vẽ các nút chức năng
        buttons = {}
        buttons["PVP"] = self.draw_rounded_button("PVP", 340)
        buttons["CREATE_ROOM"] = self.draw_rounded_button("CREATE ROOM", 405)
        buttons["JOIN_ROOM"] = self.draw_rounded_button("JOIN ROOM", 470)
        
        return buttons, ip_rect

    def draw_host_room(self, id_phong):
        self.screen.fill((255, 255, 255)) 
        self.draw_banner()
        
        font_lg = pygame.font.SysFont("tahoma", 26, bold=True)
        title = font_lg.render("Room created successfully", True, (40, 167, 69)) 
        self.screen.blit(title, title.get_rect(center=(self.width//2, 290)))
        
        sub = self.font_banner.render("Please share this code with your friends:", True, (100, 100, 100))
        self.screen.blit(sub, sub.get_rect(center=(self.width//2, 330)))
        
        box_rect = pygame.Rect(0, 0, 220, 70)
        box_rect.center = (self.width//2, 400)
        pygame.draw.rect(self.screen, (220, 240, 255), box_rect, border_radius=15) 
        pygame.draw.rect(self.screen, (0, 110, 255), box_rect, width=3, border_radius=15) 
        font_id = pygame.font.SysFont("tahoma", 45, bold=True)
        id_text = font_id.render(id_phong, True, (20, 80, 200))
        self.screen.blit(id_text, id_text.get_rect(center=box_rect.center))
        
        wait_text = self.font_small.render("Waiting for opponent to join...", True, (150, 150, 150))
        self.screen.blit(wait_text, wait_text.get_rect(center=(self.width//2, 480)))

    def draw_input_room(self, input_text):
        self.screen.fill((255, 255, 255))
        self.draw_banner()
        
        font_lg = pygame.font.SysFont("tahoma", 28, bold=True)
        title = font_lg.render("JOIN ROOM", True, (0, 110, 255))
        self.screen.blit(title, title.get_rect(center=(self.width//2, 290)))
        
        sub = self.font_banner.render("Enter room code (5 digits):", True, (100, 100, 100))
        self.screen.blit(sub, sub.get_rect(center=(self.width//2, 330)))
        
        input_box = pygame.Rect(0, 0, 250, 70)
        input_box.center = (self.width//2, 400)
        pygame.draw.rect(self.screen, (245, 245, 245), input_box, border_radius=10) 
        pygame.draw.rect(self.screen, (20, 80, 200), input_box, width=4, border_radius=10) 
        
        font_input = pygame.font.SysFont("tahoma", 40, bold=True)
        txt_surface = font_input.render(input_text, True, (0, 0, 0))
        self.screen.blit(txt_surface, txt_surface.get_rect(center=input_box.center))
        
        hint = self.font_small.render("Press ENTER to join | BACKSPACE to clear", True, (120, 120, 120))
        self.screen.blit(hint, hint.get_rect(center=(self.width//2, 480)))
        hint_esc = self.font_small.render("Press ESC to return to Menu", True, (150, 150, 150))
        self.screen.blit(hint_esc, hint_esc.get_rect(center=(self.width//2, 510)))

    def draw_error_message(self, message):
        font_loi = pygame.font.SysFont("tahoma", 18, bold=True)
        text_loi = font_loi.render(f"ERROR!: {message}", True, (220, 53, 69)) 
        self.screen.blit(text_loi, text_loi.get_rect(center=(self.width//2, 260)))

class Man_hinh_Game:
    def __init__(self, screen_width, screen_height, rows=20, cols=20):
        self.width = screen_width
        self.height = screen_height
        self.rows = rows
        self.cols = cols   
        self.bg_color = (255, 255, 255)         
        self.line_color = (226, 232, 240)      
        self.line_thickness = 1 
        self.banner_color = (0, 110, 255) 
        self.border_color = (20, 80, 200)  
        self.banner_height = 60 
        
    def draw_background(self, surface):   
        surface.fill(self.bg_color) 
        grid_start_y = self.banner_height
        grid_height = self.height - (2 * self.banner_height)
        cell_width = self.width / self.cols
        cell_height = grid_height / self.rows     
        for col in range(self.cols + 1):
            x = int(col * cell_width)
            pygame.draw.line(surface, self.line_color, (x, grid_start_y), (x, grid_start_y + grid_height), self.line_thickness)
        for row in range(self.rows + 1):
            y = int(grid_start_y + (row * cell_height))
            pygame.draw.line(surface, self.line_color, (0, y), (self.width, y), self.line_thickness)
        pygame.draw.rect(surface, self.banner_color, (0, 0, self.width, self.banner_height))  
        pygame.draw.rect(surface, self.banner_color, (0, self.height - self.banner_height, self.width, self.banner_height))  
        pygame.draw.line(surface, self.border_color, (0, self.banner_height), (self.width, self.banner_height), 4)
        pygame.draw.line(surface, self.border_color, (0, self.height - self.banner_height), (self.width, self.height - self.banner_height), 4)

    def draw_pieces(self, surface, ma_tran):
        grid_start_y = self.banner_height
        grid_height = self.height - (2 * self.banner_height)
        cell_width = self.width / self.cols
        cell_height = grid_height / self.rows
        for x in range(self.cols):
            for y in range(self.rows):
                quan_co = ma_tran[x][y]
                if quan_co != "":
                    center_x = int(x * cell_width + cell_width / 2)
                    center_y = int(grid_start_y + y * cell_height + cell_height / 2)
                    
                    piece_size = int(cell_width * 0.4)
                    
                    if quan_co == "X":
                        pygame.draw.line(surface, (200, 0, 0), (center_x - piece_size, center_y - piece_size), (center_x + piece_size, center_y + piece_size), 3)
                        pygame.draw.line(surface, (200, 0, 0), (center_x + piece_size, center_y - piece_size), (center_x - piece_size, center_y + piece_size), 3)
                    elif quan_co == "O":
                        pygame.draw.circle(surface, (0, 0, 200), (center_x, center_y), piece_size, 3)

    def draw_turn(self, surface, is_my_turn, thoi_gian):
        font = pygame.font.SysFont("tahoma", 20, bold=True)
        if is_my_turn: 
            text_surf = font.render(f"YOUR TURN! {thoi_gian}", True, (255, 255, 0))
            center_y = self.height - (self.banner_height // 2)
            rect = text_surf.get_rect(center=(self.width // 2, center_y))
            surface.blit(text_surf, rect)
        else:
            text_surf = font.render(f"Waiting for opponent... {thoi_gian}", True, (220, 220, 220))
            center_y = self.banner_height // 2
            rect = text_surf.get_rect(center=(self.width // 2, center_y))
            surface.blit(text_surf, rect)

    def draw_end_game(self, surface, ket_qua):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150) 
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        box_width, box_height = 340, 180 
        box_rect = pygame.Rect((self.width - box_width)//2, (self.height - box_height)//2, box_width, box_height)
        pygame.draw.rect(surface, (255, 255, 255), box_rect, border_radius=15) 
        pygame.draw.rect(surface, (0, 110, 255), box_rect, width=4, border_radius=15) 
        
        font_large = pygame.font.SysFont("tahoma", 32, bold=True)
        font_small = pygame.font.SysFont("tahoma", 18)
        
        if ket_qua == "thang":
            text_main = font_large.render("YOU WIN!", True, (40, 167, 69)) 
        else:
            text_main = font_large.render("GAME OVER!", True, (220, 53, 69)) 
        text_sub = font_small.render("Bạn có muốn Rematch không?", True, (100, 100, 100))
        surface.blit(text_main, text_main.get_rect(center=(self.width//2, self.height//2 - 40)))
        surface.blit(text_sub, text_sub.get_rect(center=(self.width//2, self.height//2 - 5)))
        
        btn_width, btn_height = 100, 45
        yes_rect = pygame.Rect(self.width//2 - btn_width - 15, self.height//2 + 25, btn_width, btn_height)
        no_rect = pygame.Rect(self.width//2 + 15, self.height//2 + 25, btn_width, btn_height)
        pygame.draw.rect(surface, (40, 167, 69), yes_rect, border_radius=10) 
        pygame.draw.rect(surface, (220, 53, 69), no_rect, border_radius=10) 
        
        font_btn = pygame.font.SysFont("tahoma", 16, bold=True)
        text_yes = font_btn.render("CÓ", True, (255, 255, 255))
        text_no = font_btn.render("KHÔNG", True, (255, 255, 255))
        surface.blit(text_yes, text_yes.get_rect(center=yes_rect.center))
        surface.blit(text_no, text_no.get_rect(center=no_rect.center))
        return yes_rect, no_rect

    def yeu_cau_rematch(self, surface):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150) 
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        box_width, box_height = 340, 180 
        box_rect = pygame.Rect((self.width - box_width)//2, (self.height - box_height)//2, box_width, box_height)
        pygame.draw.rect(surface, (255, 255, 255), box_rect, border_radius=15)
        pygame.draw.rect(surface, (210, 120, 50), box_rect, width=4, border_radius=15) 
        
        font_large = pygame.font.SysFont("tahoma", 28, bold=True)
        font_small = pygame.font.SysFont("tahoma", 18)
        
        text_main = font_large.render("Đối thủ muốn đấu lại!", True, (210, 120, 50)) 
        text_sub = font_small.render("Bạn có đồng ý chơi lại không?", True, (100, 100, 100))
        
        surface.blit(text_main, text_main.get_rect(center=(self.width//2, self.height//2 - 40)))
        surface.blit(text_sub, text_sub.get_rect(center=(self.width//2, self.height//2 - 5)))
        
        btn_width, btn_height = 100, 45
        yes_rect = pygame.Rect(self.width//2 - btn_width - 15, self.height//2 + 25, btn_width, btn_height)
        no_rect = pygame.Rect(self.width//2 + 15, self.height//2 + 25, btn_width, btn_height)
        
        pygame.draw.rect(surface, (40, 167, 69), yes_rect, border_radius=10) 
        pygame.draw.rect(surface, (220, 53, 69), no_rect, border_radius=10) 
        
        font_btn = pygame.font.SysFont("tahoma", 16, bold=True)
        text_yes = font_btn.render("CÓ", True, (255, 255, 255))
        text_no = font_btn.render("KHÔNG", True, (255, 255, 255))
        
        surface.blit(text_yes, text_yes.get_rect(center=yes_rect.center))
        surface.blit(text_no, text_no.get_rect(center=no_rect.center))
        
        return yes_rect, no_rect

    def da_gui_yeu_cau(self, surface):
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(150) 
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        
        box_width, box_height = 340, 150 
        box_rect = pygame.Rect((self.width - box_width)//2, (self.height - box_height)//2, box_width, box_height)
        pygame.draw.rect(surface, (255, 255, 255), box_rect, border_radius=15)
        pygame.draw.rect(surface, (0, 110, 255), box_rect, width=4, border_radius=15)
        
        font_large = pygame.font.SysFont("tahoma", 28, bold=True)
        font_small = pygame.font.SysFont("tahoma", 18)
        
        text_main = font_large.render("Đã gửi yêu cầu!", True, (0, 110, 255))
        text_sub = font_small.render("Đang chờ đối thủ phản hồi...", True, (100, 100, 100))
        
        surface.blit(text_main, text_main.get_rect(center=(self.width//2, self.height//2 - 20)))
        surface.blit(text_sub, text_sub.get_rect(center=(self.width//2, self.height//2 + 20)))

class Giao_dien_cho:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        pygame.font.init()
        self.font = pygame.font.SysFont("tahoma", 28, bold=True)
        self.font_small = pygame.font.SysFont("tahoma", 16)
        self.text = "WAITING..."
        self.angle = 0

    def update(self):
        self.angle += 4
        if self.angle >= 360:
            self.angle = 0

    def draw(self, surface):
        surface.fill((248, 250, 252))
        text_surface = self.font.render(self.text, True, (51, 65, 85))
        text_rect = text_surface.get_rect(center=(self.width // 2, self.height // 2 + 80))
        surface.blit(text_surface, text_rect) 
        hint_esc = self.font_small.render("Press ESC to back Menu", True, (150, 150, 150))
        hint_rect = hint_esc.get_rect(center=(self.width // 2, self.height // 2 + 110))
        surface.blit(hint_esc, hint_rect)
        
        center_x = self.width // 2
        center_y = self.height // 2 - 20
        spinner_radius = 40 
        num_dots = 8
        for i in range(num_dots):
            dot_angle = self.angle + (i * (360 / num_dots))
            rad = math.radians(dot_angle)
            x = center_x + spinner_radius * math.cos(rad)
            y = center_y + spinner_radius * math.sin(rad)
            dot_radius = 2 + (i * 0.8) 
            color_val = max(50, 250 - (i * 25))
            color = (59, 130, color_val) 
            pygame.draw.circle(surface, color, (int(x), int(y)), int(dot_radius))

class Network:
    def __init__(self, server_ip='127.0.0.1', port=5050):
        self.server_ip = server_ip
        self.port = port
        self.addr = (self.server_ip, self.port)
        self.message_queue = queue.Queue()
        self.is_connected = False
        self.connect()

    def connect(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect(self.addr)
            self.is_connected = True
            print(f"[NETWORK] Đã kết nối thành công tới Server {self.server_ip}:{self.port}")
            listener = threading.Thread(target=self._listen_to_server, daemon=True)
            listener.start()
            return True
        except Exception as e:
            print(f"[NETWORK LỖI] Không thể kết nối tới Server: {e}")
            self.is_connected = False
            return False

    def send(self, action, data_dict=None):
        if not self.is_connected:
            print("[NETWORK] Cảnh báo: Chưa kết nối, không thể gửi tin!")
            return
        payload = {"action": action}
        if data_dict:
            payload.update(data_dict)
        try:
            json_str = json.dumps(payload)
            message_bytes = (json_str + "\n").encode('utf-8')
            self.client.sendall(message_bytes)
        except Exception as e:
            print(f"[NETWORK LỖI] Gửi dữ liệu thất bại: {e}")
            self.is_connected = False

    def _listen_to_server(self):
        buffer = ""
        while self.is_connected:
            try:
                raw_data = self.client.recv(2048)
                if not raw_data:
                    print("[NETWORK] Mất kết nối từ Server!")
                    self.is_connected = False
                    break
                    
                buffer += raw_data.decode('utf-8')
                
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            self.message_queue.put(msg)
                        except json.JSONDecodeError:
                            print("[NETWORK] Lỗi parse JSON từ Server")
                            
            except Exception as e:
                print(f"[NETWORK] Luồng nhận dữ liệu dừng: {e}")
                self.is_connected = False
                break

    def get_events(self):
        events = []
        while not self.message_queue.empty():
            events.append(self.message_queue.get())
        return events

def main(server_ip="127.0.0.1"):
    try:
        myappid = 'gamecaro.team36.version1' 
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    global game_state
    pygame.init()
    audio_caro.init_audio()
    id_phong_hien_tai=""
    role_hien_tai=""
    bang_caro=[["" for _ in range(20)] for _ in range(20)]
    luot_cua_toi=False
    ket_qua=""
    id_text=""
    
    thong_bao_loi=""
    thoi_gian_bat_dau_luot=0
    thoi_gian_hien_loi=0 
    
    # Biến để quản lý ô nhập IP
    ip_input_text = ""
    is_ip_active = False
    ip_rect = None
    
    screen = pygame.display.set_mode((ngang_game, doc_game))
    pygame.display.set_caption("Game Caro 36 Simulation")
    
    try:
        icon_img = pygame.image.load("sounds/icon.png") 
        pygame.display.set_icon(icon_img)
    except Exception as e:
        print("Không load được icon:", e)

    menu = GiaoDien(screen)
    waiting_screen = Giao_dien_cho(ngang_game, doc_game)
    game_board = Man_hinh_Game(ngang_game, doc_game)
    clock = pygame.time.Clock()
    running = True
    menu_buttons = {}
    net=Network(server_ip=server_ip)
    
    yes_rematch=None
    no_rematch=None
    yes_rematch_2=None 
    no_rematch_2=None 

    # Hàm hỗ trợ kiểm tra và kết nối theo IP người chơi nhập
    def check_and_connect():
        nonlocal net, thong_bao_loi
        target_ip = ip_input_text.strip() if ip_input_text.strip() != "" else "127.0.0.1"
        
        # Nếu thay đổi IP -> Tạo socket mới
        if target_ip != net.server_ip:
            if net.is_connected and hasattr(net, 'client'):
                try: net.client.close()
                except: pass
            net = Network(server_ip=target_ip)
            
        if not net.is_connected:
            if not net.connect():
                thong_bao_loi = "NO SERVER"
                play_sfx("notify")
                return False
        return True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False  
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: 
                mouse_pos = event.pos
                play_sfx("click")
                
                if game_state == "MENU":
                    # Xử lý click vào ô nhập IP
                    if ip_rect and ip_rect.collidepoint(mouse_pos):
                        is_ip_active = True
                    else:
                        is_ip_active = False

                    id_phong_hien_tai = ""
                    role_hien_tai = ""
                    luot_cua_toi = False
                    ket_qua = ""
                    thong_bao_loi=""
                    id_text=""
                    bang_caro = [["" for _ in range(20)] for _ in range(20)]
                    
                    if menu_buttons.get("PVP") and menu_buttons["PVP"].collidepoint(mouse_pos):
                        if check_and_connect():
                            game_state = "WAITING"
                            net.send("tim_tran")
                    elif menu_buttons.get("CREATE_ROOM") and menu_buttons["CREATE_ROOM"].collidepoint(mouse_pos):
                        if check_and_connect():
                            game_state="OUTPUT_ID"
                            net.send("tao_phong")
                    elif menu_buttons.get("JOIN_ROOM") and menu_buttons["JOIN_ROOM"].collidepoint(mouse_pos):
                        if check_and_connect():
                            game_state="INPUT_ID"
                            id_text=""
                            thong_bao_loi=""
                            
                elif game_state == "STARTING":
                    grid_start_y = game_board.banner_height
                    grid_height = doc_game - (2 * game_board.banner_height)
                    cell_width = ngang_game / 20
                    cell_height = grid_height / 20
                    if grid_start_y <= mouse_pos[1] <= grid_start_y + grid_height:
                        grid_x = int(mouse_pos[0] // cell_width)
                        grid_y = int((mouse_pos[1] - grid_start_y) // cell_height)
                        net.send("di", {"id_phong": id_phong_hien_tai, "x": grid_x, "y": grid_y})
                        
                elif game_state == "GAME_END":
                    bang_caro=[["" for _ in range(20)] for _ in range(20)]
                    if no_rematch and no_rematch.collidepoint(mouse_pos):
                        play_sfx("click")
                        game_state = "MENU"
                        net.send("khong_muon_rematch",{"id_phong": id_phong_hien_tai} )
                    elif yes_rematch and yes_rematch.collidepoint(mouse_pos):
                        play_sfx("click")
                        game_state="WAITING_REMATCH"
                        net.send("yeu_cau_rematch", {"id_phong": id_phong_hien_tai})
                        
                elif game_state=="WANT_REMATCH":
                    bang_caro=[["" for _ in range(20)] for _ in range(20)]
                    if no_rematch_2 and no_rematch_2.collidepoint(mouse_pos):
                        play_sfx("click")
                        game_state = "MENU"
                        net.send("khong_dong_y_rematch",{"id_phong": id_phong_hien_tai})
                    elif yes_rematch_2 and yes_rematch_2.collidepoint(mouse_pos):
                        play_sfx("click")
                        net.send("dong_y_rematch",{"id_phong": id_phong_hien_tai})
                        
            if event.type == pygame.KEYDOWN:
                # Bắt phím cho ô nhập IP
                if game_state == "MENU" and is_ip_active:
                    if event.key == pygame.K_BACKSPACE:
                        ip_input_text = ip_input_text[:-1]
                    else:
                        if event.unicode in "0123456789." and len(ip_input_text) < 15:
                            ip_input_text += event.unicode

                if game_state == "WAITING":
                    if event.key==pygame.K_ESCAPE:
                        game_state="MENU"
                        net.send("huy_tim_tran")
                        
                if game_state == "INPUT_ID":
                    if event.key == pygame.K_RETURN:
                        if len(id_text)>0:
                            net.send("vao_phong", {"id_phong": id_text})
                    elif event.key == pygame.K_BACKSPACE:
                        id_text=id_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        game_state="MENU"
                    else:
                        if event.unicode.isnumeric() and len(id_text) < 5:
                            id_text += event.unicode
                            
        for msg in net.get_events():
            action = msg.get("action")
            if action=="bat_dau_game":
                game_state="STARTING"
                id_phong_hien_tai=msg.get("id_phong")
                role_hien_tai=msg.get("role")
                luot_cua_toi=msg.get("luot_cua_ban")
                thoi_gian_bat_dau_luot=pygame.time.get_ticks()
            elif action=="cap_nhat_ban_co":
                x=msg.get("x")   
                y=msg.get("y")
                bang_caro[x][y]=msg.get("quan_co") 
                luot_cua_toi = not luot_cua_toi 
                thoi_gian_bat_dau_luot=pygame.time.get_ticks()
            elif action=="game_end":
                game_state="GAME_END"
                ket_qua=msg.get("ket_qua")
                if ket_qua == "thang":
                    play_sfx("win")
                else:
                    play_sfx("lose")
            elif action== "loi":
                thong_bao_loi=msg.get("message")
                thoi_gian_hien_loi = pygame.time.get_ticks()
            elif action== "tao_phong_thanh_cong":
                id_phong_hien_tai=msg.get("id_phong")
            elif action=="dt_yeu_cau_rematch":
                game_state="WANT_REMATCH"
            elif action=="doi_thu_thoat":
                thong_bao_loi="The opponent has left."
                thoi_gian_hien_loi = pygame.time.get_ticks()
                game_state="MENU"
            elif action=="doi_thu_khong_muon_rematch":
                thong_bao_loi="The opponent refused."
                thoi_gian_hien_loi = pygame.time.get_ticks()
                game_state="MENU"
                
        if thong_bao_loi != "":
            if pygame.time.get_ticks() - thoi_gian_hien_loi > 3000: 
                thong_bao_loi = ""
                
        if game_state == "MENU":
            # Truyền tham số cho hàm draw_all
            menu_buttons, ip_rect = menu.draw_all(ip_input_text, is_ip_active) 
            if thong_bao_loi != "":
                menu.draw_error_message(thong_bao_loi)
                
        elif game_state == "WAITING":
            waiting_screen.update()
            waiting_screen.draw(screen)  
            
        elif game_state == "STARTING":
            thoi_gian_da_qua = (pygame.time.get_ticks() - thoi_gian_bat_dau_luot) // 1000
            time_left = max(0, 50 - thoi_gian_da_qua) 
            game_board.draw_background(screen)
            game_board.draw_pieces(screen,bang_caro)
            game_board.draw_turn(screen, luot_cua_toi, time_left)
            if thong_bao_loi != "":
                menu.draw_error_message(thong_bao_loi)
                
        elif game_state == "GAME_END":
            game_board.draw_background(screen) 
            game_board.draw_pieces(screen, bang_caro)
            yes_rematch, no_rematch=game_board.draw_end_game(screen,ket_qua)
            
        elif game_state=="WAITING_REMATCH":
            game_board.draw_background(screen)
            game_board.draw_pieces(screen,bang_caro)
            game_board.da_gui_yeu_cau(screen)
            
        elif game_state=="WANT_REMATCH":
            game_board.draw_background(screen)
            game_board.draw_pieces(screen,bang_caro)
            yes_rematch_2, no_rematch_2=game_board.yeu_cau_rematch(screen)
            
        elif game_state == "INPUT_ID":
            menu.draw_input_room(id_text)
            if thong_bao_loi != "":
                menu.draw_error_message(thong_bao_loi)
                
        elif game_state == "OUTPUT_ID":
            menu.draw_host_room(id_phong_hien_tai)
            
        pygame.display.flip()
        clock.tick(60)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()