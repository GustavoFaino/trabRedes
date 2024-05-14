import socket
import threading
import base64
import ast

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


def encode(msg):
    return base64.b64encode(msg.encode('utf-8'))

def decode(msg):
    print ((base64.b64decode(msg).decode('utf-8')))
    return (base64.b64decode(msg).decode('utf-8'))


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
        # RSA
        self.key = RSA.generate(1024)
        self.private_key = self.key.export_key()
        self.public_key = self.key.publickey().export_key()



    def autenticarUsuario(self, message, usuario):

        """ # Message to be encrypted
        message = b'\xbcaU\x90\xc4|q\xf1\xbdi\xfb\x00\xa3\xee e\x8a\xb0\xb3\x11E\xf661\xc7a\x90\xbb\xcd|q\xd0'

        print("1")
        # Encrypt the message
        encryptor = PKCS1_OAEP.new(RSA.import_key(self.public_key))
        print("2")
        encrypted = encryptor.encrypt(message)

        print("3")
        # Decrypt the message
        decryptor = PKCS1_OAEP.new(RSA.import_key(self.private_key))
        print("4")
        decrypted = decryptor.decrypt(encrypted)
        print("5")

        print(decrypted) """

        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return    

        usuario.client.send(encode(f'CHAVE_PUBLICA {self.public_key.decode()}'))

        print("1")
        resposta = decode(usuario.client.recv(1024)) # resposta com chave AES criptografada do cliente
        split_res = resposta.split(' ')
        while(split_res[0] != 'CHAVE_SIMETRICA'):
            resposta = decode(usuario.client.recv(1024)) # resposta com chave AES criptografada do cliente
            split_res = resposta.split(' ')

        _, encrypted_AES_key = resposta.split(' ', 1)
        print("2")

        encrypted_AES_key = bytes(ast.literal_eval(encrypted_AES_key))
        print(encrypted_AES_key)
        
        print("3")

        cipher_rsa = PKCS1_OAEP.new(RSA.import_key(self.private_key)) # descriptografando chave AES
        print("4")
        AES_key = cipher_rsa.decrypt(encrypted_AES_key)
        print("5")
        print("Decrypted data:")
        print(AES_key) 


    def broadcast(self, message):
        for usuario in self.usuarios:
            usuario.client.send(message)
    


    def criarSala(self, message, usuario):        

        split_msg = message.split(' ')
        
        if(len(split_msg) < 3):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return    

        salaAux = Sala()

        senha = ''
        nome = split_msg[2]
        tipo = split_msg[1]

        if tipo == 'PRIVADA':
            if len(split_msg) < 4:
                usuario.client.send(encode('ERRO Sala privada deve ter senha'))
                return   
            salaAux.senha = senha

        if getSala(nome, self.salas) != None:  
            usuario.client.send(encode('ERRO Já existe uma sala com esse nome')) 
            return

        elif((len(split_msg) > 3 and tipo == 'PUBLICA') or (len(split_msg) > 4 and tipo == 'PRIVADA')):
            usuario.client.send(encode('ERRO Nomes não podem ter espaços'))
            return
        
        salaAux.nome = nome
        salaAux.admin = usuario

        self.salas.append(salaAux)

        usuario.client.send(encode('CRIAR_SALA_OK'))


    
    def fecharSala(self, message, usuario):
        split_msg = message.split(' ')
        
        if(len(split_msg) < 2):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return    

        nomeSala = split_msg[1]
    
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encode('ERRO Sala non ecziste'))
            return
        
        if usuario != salaAux.admin:
            usuario.client.send(encode('ERRO Usuário não é admin'))
            return

        # removendo a sala do servidor
        index = self.salas.index(salaAux)
        self.salas.pop(index)

        # separando mensagem dos atributos do protocolo
        frase = 'SALA_FECHADA ' + nomeSala
        for usr in salaAux.usuarios:
            usr.client.send(encode(frase))




    def banirUsuario(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 3):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return

        nomeSala = split_msg[1]
    
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encode('ERRO Sala non ecziste'))
            return
        
        if usuario != salaAux.admin:
            usuario.client.send(encode('ERRO Usuário não é admin'))
            return


        nomeUsuarioBanido = split_msg[2]
        usuarioBanido = getUsuario(nomeUsuarioBanido, salaAux.usuarios)

        if usuarioBanido == None:
            usuario.client.send(encode('ERRO Usuário a ser banido não está na sala'))
            return

        index = self.salas.index(salaAux)
        self.salas[index].banidos.append(usuarioBanido)

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.remove(usuarioBanido)

        
        usuarioBanido.client.send(encode(f'BANIDO_DA_SALA {salaAux.nome}'))
        usuario.client.send(encode('BANIMENTO_OK'))

        for usr in salaAux.usuarios:
            usr.client.send(encode(f'SAIU {salaAux.nome} {usuarioBanido.nome}'))   




    def entrarSala(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return    
        
        senha = ''
        nomeSala = split_msg[1]

        if((len(split_msg) > 3)):
            usuario.client.send(encode('ERRO Muitos argumentos na mensagem'))
            return
        
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encode('ERRO Sala não existe'))
            return

        if usuario in salaAux.banidos:
            usuario.client.send(encode('ERRO Usuário foi banido da sala'))
            return

        if usuario in salaAux.usuarios:
            usuario.client.send(encode('ERRO Usuário já está na sala'))
            return

        if((len(split_msg) == 3)):
            senha = split_msg[2]

        if(salaAux.senha != '') and (salaAux.senha != senha):
            usuario.client.send(encode('ERRO Senha incorreta'))
            return

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.append(usuario)


        mensagem = 'ENTRAR_SALA_OK'
        
        for usr in salaAux.usuarios:
            mensagem = mensagem + ' ' + usr.nome
        usr.client.send(encode(mensagem))



    def sairSala(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return    
        
        nomeSala = split_msg[1]

        if((len(split_msg) > 2)):
            usuario.client.send(encode('ERRO Muitos argumentos na mensagem'))
            return
        
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encode('ERRO Sala não existe'))
            return

        if not(usuario in salaAux.usuarios):
            usuario.client.send(encode('ERRO Usuário não está na sala'))
            return

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.remove(usuario)

        
        usuario.client.send(encode('SAIR_SALA_OK'))

        for usr in salaAux.usuarios:
            usr.client.send(encode(f'SAIU {salaAux.nome} {usuario.nome}'))  
        


    def listarSalas(self, usuario):
        mensagem = 'SALAS'

        for sala in self.salas:
            mensagem = mensagem + ' ' + sala.nome
            if sala.senha == '':
                mensagem = mensagem + '[publica]'
            else:
                mensagem = mensagem + '[privada]'
        
        usuario.client.send(encode(mensagem))



    def enviarMensagem(self, message, usuario):
        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return   

        nomeSala = split_msg[1]
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encode('ERRO Sala não existe'))
            return

        if getUsuario(usuario.nome, salaAux.usuarios) == None:
            usuario.client.send(encode('ERRO Usuário não faz parte da sala'))
            return

        # separando mensagem dos atributos do protocolo
        palavras = split_msg[2:]
        frase = f'MENSAGEM {nomeSala} {usuario.nome} '
        frase = frase + ' '.join(palavras) if palavras else ''

        for usr in salaAux.usuarios:
            usr.client.send(encode(frase))   
        
    


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
            case 'AUTENTICADAO':
                print("autenticar usuario")
                self.autenticarUsuario(message, usuario)
                
        


    def handle(self, usuario):
        while True:
            try:
                message = decode(usuario.client.recv(1024))
                self.treat_message(message, usuario)
                #self.broadcast(message)
            except:
                index = self.usuarios.index(usuario)
                nome = self.usuarios[index].nome
                self.usuarios.remove(usuario)
                usuario.client.close()
                self.broadcast(encode(f'{nome} saiu do chat!'))
                break



    def register(self):
        while True:
            client, address = self.server.accept()
            print(f"Conectado com {str(address)}")
            
            message = decode(client.recv(1024))
            
            split_msg = message.split(' ') # separa a mensagem de acordo com espacos
            command = split_msg[0]

            if(command == 'REGISTRO'):
                nome = split_msg[1] # (' '.join(message.split(' ')[1:]))
                print(split_msg)
                print(nome,'res')
                
                
                if getUsuario(nome, self.usuarios) != None:
                    usuario.client.send(encode("ERRO Já existe um usuário com esse nome")) 
                    #return

                elif(len(split_msg) > 2):
                    usuario.client.send(encode("ERRO Nomes não podem ter espaços"))
                    #return

                else:     
                    usuario = Usuario(client)
                    usuario.nome = nome
                    
                    self.usuarios.append(usuario)

                    print(f"nome do cliente é {nome}!")
                    self.broadcast(encode(f"{nome} entrou no chat!"))
                    client.send(encode('REGISTRO_OK'))
                    print("regok")
                    thread = threading.Thread(target=self.handle, args=(usuario,))
                    thread.start()

                    client.send(encode('REGISTRO_OK'))


if __name__ == "__main__":
    get_host_ip()
    servidor = Servidor()
    servidor.register()

    servidor.server.close()