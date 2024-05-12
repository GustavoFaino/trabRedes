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


def usuarioExiste(nome, usuarioList):
    for usuario in usuarioList:
        if nome == usuario.username:
            return True
    return False


class Usuario:
    def __init__(self, client):
        self.username = ''
        self.client = client
        self.sala = ''


class Sala:
    def __init__(self):
        self.nome = ''
        self.senha = ''
        self.admin = ''
        self.banned = []


class Servidor:
    def __init__(self, host = '0.0.0.0', port = 12345):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.usuarios = []
        self.salas = []



    def broadcast(self, message):
        for usuario in self.usuarios:
            usuario.client.send(message)



    def criarSala(self, message, usuario):        

        split_msg = message.split(' ')
        
        if(len(split_msg) < 3):
            usuario.client.send('ERRO Mensagem falta informações'.encode('utf-8'))
            return    

        salaAux = Sala()

        senha = ''
        nome = split_msg[2]
        tipo = split_msg[1]

        if tipo == 'PRIVADA':
            if len(split_msg) < 4:
                usuario.client.send('ERRO Sala privada deve ter senha'.encode('utf-8'))
                return   
            salaAux.senha = senha

        if salaExiste(nome, self.salas):  
            usuario.client.send('ERRO Já existe uma sala com esse nome'.encode('utf-8')) 
            return

        elif((len(split_msg) > 3 and tipo == 'PUBLICA') or (len(split_msg) > 4 and tipo == 'PRIVADA')):
            usuario.client.send('ERRO Nomes não podem ter espaços'.encode('utf-8'))
            return
        
        salaAux.nome = nome
        salaAux.admin = usuario

        self.salas.append(salaAux)

        usuario.client.send('CRIAR_SALA_OK'.encode('utf-8'))


    def listarSalas(self, usuario):
        mensagem = 'SALAS'

        for sala in self.salas:
            mensagem = mensagem + ' ' + sala.nome
            if sala.senha == '':
                mensagem = mensagem + '[publica]'
            else:
                mensagem = mensagem + '[privada]'
        
        usuario.client.send(mensagem.encode('utf-8'))


    def treat_message(self, message, usuario):
        split_msg = message.split(' ') # separa a mensagem de acordo com espacos
        command = split_msg[0]

        match command:
            case 'CRIAR_SALA':
                print('criar sala')
                self.criarSala(message, usuario)
            case 'LISTAR_SALAS':
                print("listar salas")
                self.listarSalas(usuario)
                
        


    def handle(self, usuario):
        while True:
            try:
                message = usuario.client.recv(1024).decode('utf-8')
                self.treat_message(message, usuario)
                #self.broadcast(message)
            except:
                index = self.usuarios.index(usuario)
                self.usuarios.remove(usuario)
                username = self.usuarios[index].username
                usuario.close()
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
                
                
                if usuarioExiste(username, self.usuarios):#(username in self.usuarios.usernames):  
                    usuario.client.send("ERRO Já existe um usuário com esse nome".encode('utf-8')) 
                    #return

                elif(len(split_msg) > 2):
                    usuario.client.send("ERRO Nomes não podem ter espaços".encode('utf-8'))
                    #return

                else:     
                    
                    usuario = Usuario(client)
                    usuario.username = username
                    
                    self.usuarios.append(usuario)

                    print(f"username do cliente é {username}!")
                    self.broadcast(f"{username} entrou no chat!".encode('utf-8'))
                    client.send('REGISTRO_OK'.encode('utf-8'))
                    print("regok")
                    thread = threading.Thread(target=self.handle, args=(usuario,))
                    thread.start()

                    client.send('REGISTRO_OK'.encode('utf-8'))


if __name__ == "__main__":
    get_host_ip()
    servidor = Servidor()
    servidor.register()

    servidor.server.close()