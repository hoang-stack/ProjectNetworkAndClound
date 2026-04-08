import pygame

# --- TRẠNG THÁI ---
is_muted = False
sfx_dict = {}

# Đường dẫn nhạc nền 
bgm_menu_path = 'assets/menu_bgm.mp3'
bgm_match_path = 'assets/match_bgm.mp3'

def init_audio():
    """Khởi tạo mixer và tải toàn bộ hiệu ứng âm thanh vào RAM"""
    pygame.mixer.init()
    
    # Hàm con để tải âm thanh an toàn (không làm crash game nếu thiếu file)
    def load_sfx(name, filepath):
        try:
            sfx_dict[name] = pygame.mixer.Sound(filepath)
            # Chỉnh âm lượng mặc định cho hiệu ứng (0.0 đến 1.0)
            sfx_dict[name].set_volume(0.7) 
        except Exception as e:
            print(f"[CẢNH BÁO ÂM THANH] Không tìm thấy file: {filepath}")

    # Tải các hiệu ứng phát 1 lần (SFX)
    load_sfx('click', 'assets/click.wav')
    load_sfx('move', 'assets/move.wav')
    load_sfx('check', 'assets/check.wav')
    load_sfx('checkmate', 'assets/checkmate.wav')
    load_sfx('win', 'assets/win.wav')
    load_sfx('lose', 'assets/lose.wav')
    load_sfx('draw', 'assets/draw.wav')
    load_sfx('notify', 'assets/notify.wav')

def play_bgm(bgm_type):
    """Phát nhạc nền lặp đi lặp lại vô hạn"""
    global is_muted
    if is_muted:
        return
        
    try:
        if bgm_type == "menu":
            pygame.mixer.music.load(bgm_menu_path)
        elif bgm_type == "match":
            pygame.mixer.music.load(bgm_match_path)
            
        pygame.mixer.music.set_volume(0.4) # Nhạc nền nên để nhỏ thôi
        pygame.mixer.music.play(-1) # Số -1 nghĩa là lặp vô hạn
    except Exception as e:
        print(f"[CẢNH BÁO ÂM THANH] Lỗi phát nhạc nền {bgm_type}")

def play_sfx(name):
    """Phát hiệu ứng âm thanh 1 lần"""
    global is_muted
    if not is_muted and name in sfx_dict:
        sfx_dict[name].play()

def toggle_mute():
    """Bật/Tắt toàn bộ âm thanh (Dùng cho nút bấm)"""
    global is_muted
    is_muted = not is_muted
    
    if is_muted:
        pygame.mixer.music.pause() # Tạm dừng nhạc
    else:
        pygame.mixer.music.unpause() # Phát tiếp nhạc
        play_sfx('click')
        
    return is_muted # Trả về trạng thái để thay đổi hình ảnh nút

