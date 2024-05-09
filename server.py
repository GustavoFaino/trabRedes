import socket
import threading

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # Doesn't even have to be reachable
        s.connect(('8.0.0.0', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    print(ip)
    
    return ip



class Sala:
    def __init__(self, nome, admin):
        self.nome = nome
        self.senha = ''
        self.admin = admin
        self.banned = []
        self.clients = []
        clients.append(admin)



class Servidor:
    def __init__(self, host = '0.0.0.0', port = 12345):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.clients = []
        self.nicknames = []
        self.salas = []

    def broadcast(self, message):
        for client in self.clients:
            client.send(message)

    def handle(self, client):
        while True:
            try:
                message = client.recv(1024)
                self.broadcast(message)
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                nickname = self.nicknames[index]
                self.nicknames.remove(nickname)
                self.broadcast(f'{nickname} saiu do chat!'.encode('utf-8'))
                break

    def receive(self):
        while True:
            client, address = self.server.accept()
            print(f"Conectado com {str(address)}")

            
            client.send('NICK'.encode('utf-8'))
            nickname = client.recv(1024).decode('utf-8')

            if((nickname not in self.nicknames) and (" " not in nickname)):  
                self.nicknames.append(nickname)
                self.clients.append(client)

                print(f"Nickname do cliente é {nickname}!")
                self.broadcast(f"{nickname} entrou no chat!".encode('utf-8'))
                client.send('Conectado ao servidor!'.encode('utf-8'))

                thread = threading.Thread(target=self.handle, args=(client,))
                thread.start()
            
            else:
                client.send("Erro, nickname inválido".encode('utf-8'))  

if __name__ == "__main__":
    get_host_ip()
    servidor = Servidor()
    servidor.receive()

