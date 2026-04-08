import socket
import json

class Network:
    def __init__(self):
        self.server = '127.0.0.1' 
        self.port = 5555
        self.addr = (self.server, self.port)
        self.client = None

    def connect(self, ip_address=None):
        # 1. Nếu có truyền IP từ Menu vào thì cập nhật lại địa chỉ
        if ip_address and ip_address.strip() != "":
            self.server = ip_address.strip()
            self.addr = (self.server, self.port)
            
        # 2. TẠO MỚI SOCKET TRONG HÀM CONNECT
        # (Fix lỗi: Gõ sai IP lần 1 bị từ chối, gõ lại lần 2 phần mềm bị crash do socket cũ đã chết)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            self.client.connect(self.addr)
            self.client.settimeout(0.01) 
            return True
        except:
            return False

    def send(self, data):
        try:
            # Bọc JSON và thêm dấu xuống dòng \n để chống dính gói tin
            msg = json.dumps(data) + "\n"
            self.client.sendall(msg.encode('utf-8'))
        except socket.error as e:
            print(f"Lỗi gửi dữ liệu: {e}")

    def check_connection(self):
        """Hỏi thăm xem Server còn thở không bằng gói PING"""
        try:
            ping_msg = json.dumps({"type": "PING"}) + "\n"
            self.client.sendall(ping_msg.encode('utf-8'))
            return True
        except:
            return False

    def get_messages(self):
        try:
            data = self.client.recv(2048).decode('utf-8')
            
            if not data: 
                return [{"type": "SERVER_DISCONNECTED"}]
            
            messages = []
            # Tách các tin nhắn bị dính nhau
            data = data.replace('}{', '}\n{')
            
            for raw_msg in data.split('\n'):
                if raw_msg.strip():
                    messages.append(json.loads(raw_msg))
            return messages
        
        except socket.timeout:
            return []
            
        except Exception as e:
            #Rớt mạng, đứt Wi-Fi, Server sập nguồn
            print(f"[NETWORK] Rớt mạng: {e}")
            return [{"type": "SERVER_DISCONNECTED"}]