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



def getSala(nome, salaList):
    for sala in salaList:
        if nome == sala.nome:
            return sala
    return None


def getUsuario(nome, usuarioList):
    for usuario in usuarioList:
        if nome == usuario.nome:
            return usuario
    return None


class Usuario:
    def __init__(self, client):
        self.nome = ''
        self.client = client


class Sala:
    def __init__(self):
        self.nome = ''
        self.senha = ''
        self.admin = ''
        self.banidos = []
        self.usuarios = []


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

        if getSala(nome, self.salas) != None:  
            usuario.client.send('ERRO Já existe uma sala com esse nome'.encode('utf-8')) 
            return

        elif((len(split_msg) > 3 and tipo == 'PUBLICA') or (len(split_msg) > 4 and tipo == 'PRIVADA')):
            usuario.client.send('ERRO Nomes não podem ter espaços'.encode('utf-8'))
            return
        
        salaAux.nome = nome
        salaAux.admin = usuario

        self.salas.append(salaAux)

        usuario.client.send('CRIAR_SALA_OK'.encode('utf-8'))


    
    def fecharSala(self, message, usuario):
        split_msg = message.split(' ')
        
        if(len(split_msg) < 2):
            usuario.client.send('ERRO Mensagem falta informações'.encode('utf-8'))
            return    

        nomeSala = split_msg[1]
    
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send('ERRO Sala non ecziste'.encode('utf-8'))
            return
        
        if usuario != salaAux.admin:
            usuario.client.send('ERRO Usuário não é admin'.encode('utf-8'))
            return

        # removendo a sala do servidor
        index = self.salas.index(salaAux)
        self.salas.pop(index)

        # separando mensagem dos atributos do protocolo
        frase = 'SALA_FECHADA ' + nomeSala
        for usr in salaAux.usuarios:
            usr.client.send(frase.encode('utf-8'))




    def banirUsuario(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 3):
            usuario.client.send('ERRO Mensagem falta informações'.encode('utf-8'))
            return

        nomeSala = split_msg[1]
    
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send('ERRO Sala non ecziste'.encode('utf-8'))
            return
        
        if usuario != salaAux.admin:
            usuario.client.send('ERRO Usuário não é admin'.encode('utf-8'))
            return


        nomeUsuarioBanido = split_msg[2]
        usuarioBanido = getUsuario(nomeUsuarioBanido, salaAux.usuarios)

        if usuarioBanido == None:
            usuario.client.send('ERRO Usuário a ser banido não está na sala'.encode('utf-8'))
            return

        index = self.salas.index(salaAux)
        self.salas[index].banidos.append(usuarioBanido)

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.remove(usuarioBanido)

        
        usuarioBanido.client.send(f'BANIDO_DA_SALA {salaAux.nome}'.encode('utf-8'))
        usuario.client.send('BANIMENTO_OK'.encode('utf-8'))

        for usr in salaAux.usuarios:
            usr.client.send(f'SAIU {salaAux.nome} {usuarioBanido.nome}'.encode('utf-8'))   




    def entrarSala(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send('ERRO Mensagem falta informações'.encode('utf-8'))
            return    
        
        senha = ''
        nomeSala = split_msg[1]

        if((len(split_msg) > 3)):
            usuario.client.send('ERRO Muitos argumentos na mensagem'.encode('utf-8'))
            return
        
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send('ERRO Sala não existe'.encode('utf-8'))
            return

        if usuario in salaAux.banidos:
            usuario.client.send('ERRO Usuário foi banido da sala'.encode('utf-8'))
            return

        if usuario in salaAux.usuarios:
            usuario.client.send('ERRO Usuário já está na sala'.encode('utf-8'))
            return

        if((len(split_msg) == 3)):
            senha = split_msg[2]

        if(salaAux.senha != '') and (salaAux.senha != senha):
            usuario.client.send('ERRO Senha incorreta'.encode('utf-8'))
            return

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.append(usuario)


        mensagem = 'ENTRAR_SALA_OK'
        
        for usr in salaAux.usuarios:
            mensagem = mensagem + ' ' + usr.nome
        usr.client.send(mensagem.encode('utf-8'))



    def sairSala(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send('ERRO Mensagem falta informações'.encode('utf-8'))
            return    
        
        nomeSala = split_msg[1]

        if((len(split_msg) > 2)):
            usuario.client.send('ERRO Muitos argumentos na mensagem'.encode('utf-8'))
            return
        
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send('ERRO Sala não existe'.encode('utf-8'))
            return

        if not(usuario in salaAux.usuarios):
            usuario.client.send('ERRO Usuário não está na sala'.encode('utf-8'))
            return

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.remove(usuario)

        
        usuario.client.send('SAIR_SALA_OK'.encode('utf-8'))

        for usr in salaAux.usuarios:
            usr.client.send(f'SAIU {salaAux.nome} {usuario.nome}'.encode('utf-8'))  
        


    def listarSalas(self, usuario):
        mensagem = 'SALAS'

        for sala in self.salas:
            mensagem = mensagem + ' ' + sala.nome
            if sala.senha == '':
                mensagem = mensagem + '[publica]'
            else:
                mensagem = mensagem + '[privada]'
        
        usuario.client.send(mensagem.encode('utf-8'))



    def enviarMensagem(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send('ERRO Mensagem falta informações'.encode('utf-8'))
            return   

        nomeSala = split_msg[1]
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send('ERRO Sala não existe'.encode('utf-8'))
            return

        if getUsuario(usuario.nome, salaAux.usuarios) == None:
            usuario.client.send('ERRO Usuário não faz parte da sala'.encode('utf-8'))
            return

        # separando mensagem dos atributos do protocolo
        palavras = split_msg[2:]
        frase = f'MENSAGEM {nomeSala} {usuario.nome} '
        frase = frase + ' '.join(palavras) if palavras else ''

        for usr in salaAux.usuarios:
            usr.client.send(frase.encode('utf-8'))   
        
        


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
            case 'ENTRAR_SALA':
                print("entrar sala")
                self.entrarSala(message, usuario)
            case 'SAIR_SALA':
                print("sair sala")
                self.entrarSala(message, usuario)
            case 'ENVIAR_MENSAGEM':
                print("enviar mensagem")
                self.enviarMensagem(message, usuario)
            case 'FECHAR_SALA':
                print("fechar sala")
                self.fecharSala(message, usuario)
            case 'BANIR_USUARIO':
                print("banir usuario")
                self.banirUsuario(message, usuario)
                
        


    def handle(self, usuario):
        while True:
            try:
                message = usuario.client.recv(1024).decode('utf-8')
                self.treat_message(message, usuario)
                #self.broadcast(message)
            except:
                index = self.usuarios.index(usuario)
                nome = self.usuarios[index].nome
                self.usuarios.remove(usuario)
                usuario.client.close()
                self.broadcast(f'{nome} saiu do chat!'.encode('utf-8'))
                break



    def register(self):
        while True:
            client, address = self.server.accept()
            print(f"Conectado com {str(address)}")
            
            message = client.recv(1024).decode('utf-8')
            
            split_msg = message.split(' ') # separa a mensagem de acordo com espacos
            command = split_msg[0]

            if(command == 'REGISTRO'):
                nome = split_msg[1] # (' '.join(message.split(' ')[1:]))
                print(split_msg)
                print(nome,'res')
                
                
                if getUsuario(nome, self.usuarios) != None:#(nome in self.usuarios.nomes):  
                    usuario.client.send("ERRO Já existe um usuário com esse nome".encode('utf-8')) 
                    #return

                elif(len(split_msg) > 2):
                    usuario.client.send("ERRO Nomes não podem ter espaços".encode('utf-8'))
                    #return

                else:     
                    
                    usuario = Usuario(client)
                    usuario.nome = nome
                    
                    self.usuarios.append(usuario)

                    print(f"nome do cliente é {nome}!")
                    self.broadcast(f"{nome} entrou no chat!".encode('utf-8'))
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