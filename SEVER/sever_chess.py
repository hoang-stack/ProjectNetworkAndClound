import socket
import threading
import chess
import random
import string
import json

# HOST = '0.0.0.0'   # Báo cho Server biết: "Ai bắt chung Wi-Fi đều được phép vào!"  
HOST = '127.0.0.1' # TEST local
PORT = 5555

# --- CÁC BIẾN QUẢN LÝ TOÀN CỤC ---  
clients = {} 
player_counter = 1
pvp_queue = []
rooms = {}

# --- HÀM TẠO ID DUY NHẤT ---
def generate_player_id():
    global player_counter
    pid = f"P{player_counter:05d}" 
    player_counter += 1
    return pid

def generate_room_code():
    return ''.join(random.choices(string.digits, k=5))

# --- HÀM GỬI TIN NHẮN ---
def send_to(client_socket, msg_dict):
    try:
        msg = json.dumps(msg_dict) + "\n" 
        client_socket.sendall(msg.encode('utf-8'))
    except:
        pass

# --- XỬ LÝ TỪNG CLIENT RIÊNG BIỆT ---
def handle_client(conn, addr):
    global pvp_queue
    pid = generate_player_id()
    clients[pid] = {"socket": conn, "name": "Unknown", "room": None}
    print(f"[+] Client kết nối: {pid} ({addr})")

    send_to(conn, {"type": "WELCOME", "id": pid})

    try:
        while True:
            data = conn.recv(2048).decode('utf-8')
            if not data: break
            
            # ---> TUYỆT CHIÊU CHỐNG DÍNH GÓI TIN <---
            data = data.replace('}{', '}\n{')
            
            for raw_msg in data.split('\n'):
                if raw_msg.strip() == '': continue
                
                try:
                    msg = json.loads(raw_msg)
                    msg_type = msg.get("type")

                    # BỎ QUA LỆNH PING CỦA CLIENT
                    if msg_type == "PING":
                        continue 

                    # XỬ LÝ TIN NHẮN
                    process_message(pid, msg)
                except json.JSONDecodeError:
                    print(f"[-] Lỗi giải mã JSON từ {pid}: {raw_msg}")

    except Exception as e:
        print(f"[-] Client ngắt kết nối: {pid} ({e})")
    finally:
        if pid in pvp_queue:
            pvp_queue.remove(pid)
        
        room_id = clients[pid]["room"]
        if room_id and room_id in rooms:
            room = rooms[room_id]
            other_pid = room["p2"] if room["p1"] == pid else room["p1"]
            if other_pid and other_pid in clients:
                send_to(clients[other_pid]["socket"], {"type": "OPPONENT_DISCONNECTED"})
            del rooms[room_id]
            
        del clients[pid]
        conn.close()

# --- BỘ ĐỊNH TUYẾN TIN NHẮN TỪ CLIENT ---
def process_message(pid, msg):
    global pvp_queue, rooms
    msg_type = msg.get("type")
    
    if msg_type == "SET_NAME":
        clients[pid]["name"] = msg.get("name")
        print(f"[*] {pid} đổi tên thành: {msg.get('name')}")

    elif msg_type == "FIND_PVP":
        if pid not in pvp_queue:
            pvp_queue.append(pid)
            print(f"[*] {pid} đang tìm trận PVP...")
        
        if len(pvp_queue) >= 2:
            p1_id = pvp_queue.pop(0)
            p2_id = pvp_queue.pop(0)
            if random.choice([True, False]):
                p1_id, p2_id = p2_id, p1_id
            create_game_room(p1_id, p2_id, is_private=False)

    elif msg_type == "CANCEL_PVP":
        if pid in pvp_queue:
            pvp_queue.remove(pid)
            print(f"[*] {pid} đã hủy tìm trận.")

    elif msg_type == "CREATE_ROOM":
        room_code = generate_room_code()
        rooms[room_code] = {"p1": pid, "p2": None, "board": chess.Board()}
        clients[pid]["room"] = room_code
        print(f"[*] {pid} tạo phòng riêng: {room_code}")
        send_to(clients[pid]["socket"], {"type": "ROOM_CREATED", "room_code": room_code})

    elif msg_type == "JOIN_ROOM":
        room_code = msg.get("room_code")
        if room_code in rooms:
            room = rooms[room_code]
            if room["p2"] is None:
                room["p2"] = pid
                p1_id, p2_id = room["p1"], pid
                if random.choice([True, False]):
                    room["p1"], room["p2"] = p2_id, p1_id
                    p1_id, p2_id = room["p1"], room["p2"]
                
                print(f"[*] {pid} đã vào phòng {room_code}")
                create_game_room(p1_id, p2_id,is_private=True, room_id=room_code)
            else:
                send_to(clients[pid]["socket"], {"type": "ERROR", "msg": "Phòng đã đầy!"})
        else:
            send_to(clients[pid]["socket"], {"type": "ERROR", "msg": "Phòng không tồn tại!"})

    else:
        room_id = clients[pid]["room"]
        if not room_id or room_id not in rooms:
            return 

        room = rooms[room_id]
        other_pid = room["p2"] if room["p1"] == pid else room["p1"]
        other_socket = clients[other_pid]["socket"]

        if msg_type == "MOVE":
            move_str = msg.get("move")
            move = chess.Move.from_uci(move_str)
            if move in room["board"].legal_moves:
                room["board"].push(move)
                
                send_to(other_socket, {"type": "MOVE", "move": move_str})
                send_to(clients[pid]["socket"], {"type": "MOVE", "move": move_str})
                
                if room["board"].is_game_over():
                    res = room["board"].result() 
                    end_msg = {"type": "GAME_OVER", "result": res}
                    send_to(clients[pid]["socket"], end_msg)
                    send_to(other_socket, end_msg)
            else:
                send_to(clients[pid]["socket"], {"type": "ERROR", "msg": "Nước đi sai luật!"})

        elif msg_type == "CHAT":
            send_to(other_socket, {"type": "CHAT", "sender": clients[pid]["name"], "text": msg.get("text")})

        elif msg_type == "SURRENDER":
            print(f"[*] {pid} đã đầu hàng trong phòng {room_id}")
            send_to(other_socket, {"type": "OPPONENT_SURRENDERED"})

        elif msg_type == "TIMEOUT":
            print(f"[*] {pid} đã hết thời gian trong phòng {room_id}")
            send_to(other_socket, {"type": "OPPONENT_TIMEOUT"})

        elif msg_type == "OFFER_DRAW":
            send_to(other_socket, {"type": "DRAW_OFFERED"})

        elif msg_type == "DRAW_RESPONSE":
            if msg.get("accepted"):
                end_msg = {"type": "GAME_OVER", "result": "1/2-1/2"}
                send_to(clients[pid]["socket"], end_msg)
                send_to(other_socket, end_msg)
            else:
                send_to(other_socket, {"type": "DRAW_DECLINED"})
                
        elif msg_type == "REQUEST_REMATCH":
            send_to(other_socket, {"type": "REMATCH_REQUESTED"})
            
        elif msg_type == "ACCEPT_REMATCH":
            room["board"].reset() 
            send_to(clients[pid]["socket"], {"type": "REMATCH_ACCEPTED"})
            send_to(other_socket, {"type": "REMATCH_ACCEPTED"})
            
        elif msg_type == "DECLINE_REMATCH":
            send_to(other_socket, {"type": "REMATCH_DECLINED"})
            
        elif msg_type == "LEAVE_ROOM":
            send_to(other_socket, {"type": "OPPONENT_DISCONNECTED"})
            if room_id in rooms: del rooms[room_id]

def create_game_room(p1_id, p2_id, is_private=False, room_id=None):
    global rooms
    if not is_private:
        room_id = generate_room_code()
        rooms[room_id] = {"p1": p1_id, "p2": p2_id, "board": chess.Board()}
    
    clients[p1_id]["room"] = room_id
    clients[p2_id]["room"] = room_id

    name1 = clients[p1_id]["name"]
    name2 = clients[p2_id]["name"]

    send_to(clients[p1_id]["socket"], {"type": "MATCHED", "color": "WHITE", "opponent": name2})
    send_to(clients[p2_id]["socket"], {"type": "MATCHED", "color": "BLACK", "opponent": name1})
    print(f"[GAME] Trận đấu bắt đầu tại {room_id}: {name1} (Trắng) vs {name2} (Đen)")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Đang trực tại cổng {PORT} (Version JSON Routing)...")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()