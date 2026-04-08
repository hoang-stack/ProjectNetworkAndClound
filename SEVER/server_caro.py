import socket
import threading
import json
import random
import time
HOST="0.0.0.0"
PORT=5050

hang_cho_client=[]
cac_phong=[]
phonghd={}

server=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST,PORT))
lock=threading.Lock()
def tao_id():
    global phonghd
    while True:
        id_str = str(random.randint(10000, 99999)) # Ép kiểu thành chữ luôn
        if id_str not in phonghd:
            return id_str
def gui_tin_nhan(conn, dict_du_lieu):
    try:
        chuoi_json = json.dumps(dict_du_lieu)
        conn.sendall((chuoi_json + "\n").encode("utf-8"))
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")

def check_win(ban_co,x,y,quan_co):
    cac_huong = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dx, dy in cac_huong:
        dem = 1 
        
        tx, ty = x + dx, y + dy
        while 0 <= tx < 20 and 0 <= ty < 20 and ban_co[tx][ty] == quan_co:
            dem += 1
            tx += dx
            ty += dy
            
        
        tx, ty = x - dx, y - dy
        while 0 <= tx < 20 and 0 <= ty < 20 and ban_co[tx][ty] == quan_co:
            dem += 1
            tx -= dx
            ty -= dy
            
        
        if dem >= 5:
            return True
            
    return False
def xu_ly_tim_tran(conn):
    global hang_cho_client, phonghd, lock
    with lock:
        if conn not in hang_cho_client:
            hang_cho_client.append(conn)
        if len(hang_cho_client)>=2:
            nguoi_choi_1=hang_cho_client.pop(0)
            nguoi_choi_2=hang_cho_client.pop(0)
            id_phong=tao_id()
            ban_co_trong = [["" for _ in range(20)] for _ in range(20)]
            phonghd[id_phong]={
                "nguoi_choi": [nguoi_choi_1,nguoi_choi_2],
                "ban_co":ban_co_trong,
                "luot_hien_tai":nguoi_choi_1,
                "quan_co": {nguoi_choi_1: "X", nguoi_choi_2: "O"},
                "thoi_gian_bat_dau": time.time()
            }
            print("ghep tran xong")
            gui_tin_nhan(nguoi_choi_1,{
                "action": "bat_dau_game",
                "id_phong": id_phong,
                "role": "X",
                "luot_cua_ban": True
            })
            gui_tin_nhan(nguoi_choi_2, {
                "action": "bat_dau_game",
                "id_phong": id_phong,
                "role": "O",
                "luot_cua_ban": False
            })
            
def xu_ly_huy_tim_tran(conn):
    global hang_cho_client, lock
    with lock:
        if conn in hang_cho_client:
            hang_cho_client.remove(conn)
            print("Một người chơi đã hủy tìm trận. Đã xóa khỏi hàng chờ.")
def xu_ly_tao_phong(conn):
    global phonghd, lock
    with lock:
        id_phong=tao_id()
        ban_co_trong = [["" for _ in range(20)] for _ in range(20)]
        phonghd[id_phong]={
            "nguoi_choi": [conn],
            "ban_co":ban_co_trong,
            "luot_hien_tai":conn,
            "quan_co": {conn: "X"}
        }
        
        print(f"phong duoc tao {id_phong}")
        gui_tin_nhan(conn,{
            "action": "tao_phong_thanh_cong",
            "id_phong": id_phong
        })
def xu_ly_vao_phong(conn, id_phong):
    global phonghd, lock
    with lock:
        if id_phong in phonghd:
            phong = phonghd[id_phong]
            if len(phong["nguoi_choi"]) == 1:
                phong["nguoi_choi"].append(conn)
                phong["quan_co"][conn]="O"
                print(f"Phòng {id_phong} đã đủ người. Bắt đầu game!")
                
                nguoi_tao_phong = phong["nguoi_choi"][0]
                nguoi_vao_phong = phong["nguoi_choi"][1] 
                
                gui_tin_nhan(nguoi_tao_phong, {
                    "action": "bat_dau_game",
                    "id_phong": id_phong,
                    "role": "X",
                    "luot_cua_ban": True
                })
                
                
                gui_tin_nhan(nguoi_vao_phong, {
                    "action": "bat_dau_game",
                    "id_phong": id_phong,
                    "role": "O",
                    "luot_cua_ban": False
                })
            else:
                
                gui_tin_nhan(conn, {
                    "action": "loi",
                    "message": "Phòng này đã đầy, trận đấu đang diễn ra!"
                })
        else:
            gui_tin_nhan(conn, {
                "action": "loi",
                "message": "Không tìm thấy phòng với ID này!"
            })
        
def xu_ly_nuoc_di(conn,id_phong,x,y):
    global phonghd, lock
    with lock: 
        if id_phong not in phonghd:
            return    
        phong = phonghd[id_phong]
        nguoi_choi_1, nguoi_choi_2 = phong["nguoi_choi"]
        doi_thu = nguoi_choi_2 if conn == nguoi_choi_1 else nguoi_choi_1
        if phong["luot_hien_tai"] != conn:
            gui_tin_nhan(conn, {"action": "loi", "message": "chua den luot"})
            return
        if phong["ban_co"][x][y] != "":
            gui_tin_nhan(conn, {"action": "loi", "message": "o da co chu"})
            return
        quan_co_cua_toi = phong["quan_co"][conn]
        phong["ban_co"][x][y] = quan_co_cua_toi 
        tin_nhan_cap_nhat = {
            "action": "cap_nhat_ban_co",
            "x": x,
            "y": y,
            "quan_co": quan_co_cua_toi
        }
        gui_tin_nhan(conn, tin_nhan_cap_nhat)
        gui_tin_nhan(doi_thu, tin_nhan_cap_nhat)
        if check_win(phong["ban_co"], x, y, quan_co_cua_toi):
            print(f"Game Over ở phòng {id_phong}. Người thắng: {quan_co_cua_toi}")
            gui_tin_nhan(conn, {"action": "game_end", "ket_qua": "thang"})
            gui_tin_nhan(doi_thu, {"action": "game_end", "ket_qua": "thua"})
              
        else:
            phong["luot_hien_tai"] = doi_thu
            phong["thoi_gian_bat_dau"]=time.time()
def xu_ly_ngat_ket_noi(conn):
    global hang_cho_client, phonghd, lock
    with lock:
        if conn in hang_cho_client:
            hang_cho_client.remove(conn)
        phong_can_xoa = []
        for id_phong, phong in phonghd.items():
            if conn in phong["nguoi_choi"]:
                if len(phong["nguoi_choi"]) == 2:
                    nguoi_choi_1, nguoi_choi_2 = phong["nguoi_choi"]
                    doi_thu = nguoi_choi_2 if conn == nguoi_choi_1 else nguoi_choi_1
                    gui_tin_nhan(doi_thu, {"action": "game_end", "ket_qua": "thang"})
                phong_can_xoa.append(id_phong)
        for id_phong in phong_can_xoa:
            del phonghd[id_phong]
def xu_ly_khong_muon_rematch(conn, id_phong):
    global phonghd, lock
    with lock:
        if id_phong in phonghd:
            del phonghd[id_phong]
def xu_ly_yeu_cau_rematch_nhan(conn, id_phong):
    global phonghd, lock
    with lock:
        if id_phong not in phonghd:
            gui_tin_nhan(conn, {"action": "doi_thu_thoat"})
        else:
            phong = phonghd[id_phong]
            for i in phong["nguoi_choi"]:
                if i != conn:
                    gui_tin_nhan(i, {"action": "dt_yeu_cau_rematch"})
def xu_ly_khong_dong_y_rematch(conn, id_phong):
    global phonghd, lock
    with lock:
        if id_phong in phonghd:
            phong = phonghd[id_phong]
            for i in phong["nguoi_choi"]:
                if i != conn:
                    gui_tin_nhan(i, {"action": "doi_thu_khong_muon_rematch"})
            del phonghd[id_phong]
def xu_ly_rematch(conn,id_phong):
    global phonghd, lock
    if id_phong not in phonghd: 
            return
        
    phong = phonghd[id_phong]
    nguoi1, nguoi2 = phong["nguoi_choi"]
        
    phong["ban_co"] = [["" for _ in range(20)] for _ in range(20)]
    phong["thoi_gian_bat_dau"] = time.time()
        
    phong["quan_co"][nguoi1] = "O"
    phong["quan_co"][nguoi2] = "X"
    phong["luot_hien_tai"] = nguoi2  
        
    gui_tin_nhan(nguoi1, {
        "action": "bat_dau_game",
        "id_phong": id_phong,
        "role": "O",
        "luot_cua_ban": False
    })
    gui_tin_nhan(nguoi2, {
        "action": "bat_dau_game",
        "id_phong": id_phong,
        "role": "X",
        "luot_cua_ban": True
    })
def xu_ly_client(conn, addr): 
    global phonghd
    print(f"Xu ly {addr}")
    dulieu=""
    while True:
        try:
            data=conn.recv(1024)
            if not data:
                print("ngat ket noi")
                xu_ly_ngat_ket_noi(conn)
                break
            dulieu+=data.decode("utf-8")
            while "\n" in dulieu:
                dulieuchuan, dulieu=dulieu.split('\n',1)
                if not dulieuchuan.strip():
                    continue
                try:
                    dulieuchuan=json.loads(dulieuchuan)
                    action=dulieuchuan.get("action")
                    if action=="tim_tran":
                        xu_ly_tim_tran(conn)
                    elif action=="tao_phong":
                        xu_ly_tao_phong(conn)
                    elif action=="vao_phong":
                        id_phong=dulieuchuan.get("id_phong")
                        xu_ly_vao_phong(conn,id_phong)
                    elif action=="di":
                        x=dulieuchuan.get("x")
                        y=dulieuchuan.get("y")
                        id_phong=dulieuchuan.get("id_phong")
                        xu_ly_nuoc_di(conn,id_phong,x,y) 
                    elif action=="huy_tim_tran":
                        xu_ly_huy_tim_tran(conn)
                    elif action== "khong_muon_rematch":
                        id_phong=dulieuchuan.get("id_phong")
                        xu_ly_khong_muon_rematch(conn,id_phong)
                    elif action=="yeu_cau_rematch":
                        id_phong=dulieuchuan.get("id_phong")
                        xu_ly_yeu_cau_rematch_nhan(conn,id_phong)
                    elif action=="khong_dong_y_rematch":
                        id_phong=dulieuchuan.get("id_phong")
                        xu_ly_khong_dong_y_rematch(conn,id_phong)
                    elif action=="dong_y_rematch":
                        id_phong=dulieuchuan.get("id_phong")
                        xu_ly_rematch(conn,id_phong)
                except json.JSONDecodeError:
                    print(f"loi json")
        except Exception as e:
            print(f"[ERROR] Lỗi đột xuất với {addr}: {e}")
            xu_ly_ngat_ket_noi(conn)
            break
def kiem_tra_timeout():
    global phonghd, lock
    THOI_GIAN_MAX = 50 
    while True:
        time.sleep(1) # Cứ 1 giây kiểm tra 1 lần
        with lock:
            hien_tai = time.time()
            phong_can_xoa = []
            for id_phong, phong in phonghd.items():
                if len(phong["nguoi_choi"]) == 2:
                    thoi_gian_da_qua = hien_tai - phong.get("thoi_gian_bat_dau", hien_tai)
                    if thoi_gian_da_qua > THOI_GIAN_MAX:
                        ke_cham_chap = phong["luot_hien_tai"]
                        nguoi_choi_1, nguoi_choi_2 = phong["nguoi_choi"]
                        nguoi_thang = nguoi_choi_2 if ke_cham_chap == nguoi_choi_1 else nguoi_choi_1
                        gui_tin_nhan(ke_cham_chap, {"action": "game_end", "ket_qua": "thua"})
                        gui_tin_nhan(nguoi_thang, {"action": "game_end", "ket_qua": "thang"})
                        phong_can_xoa.append(id_phong)
            for id_phong in phong_can_xoa:
                del phonghd[id_phong]

def start():
    server.listen()
    print(f"Đang trực tại {PORT}")
    threading.Thread(target=kiem_tra_timeout,daemon=True).start()
    while True:
        conn,addr= server.accept()
        print(f"ket noi nguoi choi {addr}")
        threading.Thread(target=xu_ly_client, args=(conn,addr), daemon=True).start()
start()


    

