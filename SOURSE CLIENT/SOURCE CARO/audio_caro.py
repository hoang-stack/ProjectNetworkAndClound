import pygame
import os
import sys
def duong_dan(relative_path):
    try:
        base_path=sys._MEIPASS
    except:
        base_path=os.path.abspath(".")
    return os.path.join(base_path, relative_path)
    
# --- TRẠNG THÁI ---
is_muted = False
sfx_dict = {}

# Đường dẫn nhạc nền 
##bgm_match_path = 'assets/match_bgm.mp3'

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
    load_sfx('click', duong_dan('sounds/click.wav'))
    load_sfx('win', duong_dan('sounds/win.wav'))
    load_sfx('lose', duong_dan('sounds/lose.wav'))
    load_sfx('notify', duong_dan('sounds/notify.wav'))
def play_sfx(name):
    """Phát hiệu ứng âm thanh 1 lần"""
    global is_muted
    if not is_muted and name in sfx_dict:
        sfx_dict[name].play()
