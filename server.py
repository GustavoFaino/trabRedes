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



def salaExiste(nome, salaList):
    for sala in salaList:
        if nome == sala.nome:
            return True
    return False


class Sala:
    def __init__(self):
        self.nome = ''
        self.senha = ''
        self.admin = ''
        self.banned = []
        self.clients = []



class Servidor:
    def __init__(self, host = '0.0.0.0', port = 12345):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.clients = []
        self.usernames = []
        self.salas = []



    def broadcast(self, message):
        for client in self.clients:
            client.send(message)



    def criarSala(self, message, client):        

        split_msg = message.split(' ')
        
        if(len(split_msg) < 3):
            client.send('ERRO Mensagem falta informações'.encode('utf-8'))
            return    

        salaAux = Sala()

        senha = ''
        nome = split_msg[2]
        tipo = split_msg[1]

        if tipo == 'PRIVADA':
            if len(split_msg) < 4:
                client.send('ERRO Sala privada deve ter senha'.encode('utf-8'))
                return   
            salaAux.senha = senha

        if salaExiste(nome, self.salas):  
            client.send('ERRO Já existe uma sala com esse nome'.encode('utf-8')) 
            return

        elif((len(split_msg) > 3 and tipo == 'PUBLICA') or (len(split_msg) > 4 and tipo == 'PRIVADA')):
            client.send('ERRO Nomes não podem ter espaços'.encode('utf-8'))
            return
        
        salaAux.nome = nome
        salaAux.admin = client

        self.salas.append(salaAux)

        client.send('CRIAR_SALA_OK'.encode('utf-8'))


    def listarSalas(self, client):
        mensagem = 'SALAS'

        for sala in self.salas:
            mensagem = mensagem + ' ' + sala.nome
            if sala.senha == '':
                mensagem = mensagem + '[publica]'
            else:
                mensagem = mensagem + '[privada]'
        
        client.send(mensagem.encode('utf-8'))


    def treat_message(self, message, client):
        split_msg = message.split(' ') # separa a mensagem de acordo com espacos
        command = split_msg[0]

        match command:
            case 'CRIAR_SALA':
                print('criar sala')
                self.criarSala(message, client)
            case 'LISTAR_SALAS':
                print("listar salas")
                self.listarSalas(client)
                
        


    def handle(self, client):
        while True:
            try:
                message = client.recv(1024).decode('utf-8')
                self.treat_message(message, client)
                #self.broadcast(message)
            except:
                index = self.clients.index(client)
                self.clients.remove(client)
                client.close()
                username = self.usernames[index]
                self.usernames.remove(username)
                self.broadcast(f'{username} saiu do chat!'.encode('utf-8'))
                break



    def register(self):
        while True:
            client, address = self.server.accept()
            print(f"Conectado com {str(address)}")
            
            message = client.recv(1024).decode('utf-8')
            
            split_msg = message.split(' ') # separa a mensagem de acordo com espacos
            command = split_msg[0]

            if(command == 'REGISTRO'):
                username = split_msg[1] # (' '.join(message.split(' ')[1:]))
                print(split_msg)
                print(username,'res')
                
                if(username in self.usernames):  
                    client.send("ERRO Já existe um usuário com esse nome".encode('utf-8')) 
                    #return

                elif(len(split_msg) > 2):
                    client.send("ERRO Nomes não podem ter espaços".encode('utf-8'))
                    #return

                else:     
                    self.usernames.append(username)
                    self.clients.append(client)

                    print(f"username do cliente é {username}!")
                    self.broadcast(f"{username} entrou no chat!".encode('utf-8'))
                    client.send('REGISTRO_OK'.encode('utf-8'))
                    print("regok")
                    thread = threading.Thread(target=self.handle, args=(client,))
                    thread.start()

                    client.send('REGISTRO_OK'.encode('utf-8'))


if __name__ == "__main__":
    get_host_ip()
    servidor = Servidor()
    servidor.register()

    servidor.server.close()