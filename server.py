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


def encryptAES(plaintext, key):
    # Create an AES cipher object with the key and AES.MODE_ECB mode
    cipher = AES.new(key, AES.MODE_ECB)
    # Pad the plaintext and encrypt it
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    return ciphertext
 
def decryptAES(ciphertext, key):
    # Create an AES cipher object with the key and AES.MODE_ECB mode
    cipher = AES.new(key, AES.MODE_ECB)
    # Decrypt the ciphertext and remove the padding
    decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return decrypted_data


def encode(msg):
    return base64.b64encode(msg.encode('utf-8'))

def decode(msg):
    #print ((base64.b64decode(msg).decode('utf-8')))
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
        self.AES_key = b''


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

        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encode('ERRO Mensagem falta informações'))
            return    

        usuario.client.send(encode(f'CHAVE_PUBLICA {self.public_key.decode()}'))

        resposta = decode(usuario.client.recv(1024)) # resposta com chave AES criptografada do cliente
        split_res = resposta.split(' ')
        while(split_res[0] != 'CHAVE_SIMETRICA'):
            resposta = decode(usuario.client.recv(1024)) # resposta com chave AES criptografada do cliente
            split_res = resposta.split(' ')

        _, encrypted_AES_key = resposta.split(' ', 1)

        encrypted_AES_key = bytes(ast.literal_eval(encrypted_AES_key))
        
        cipher_rsa = PKCS1_OAEP.new(RSA.import_key(self.private_key)) # descriptografando chave AES
        AES_key = cipher_rsa.decrypt(encrypted_AES_key)

        # guardando chave AES no usuario
        index = self.usuarios.index(usuario)
        self.usuarios[index].AES_key = AES_key  
        

    def broadcast(self, message):
        for usuario in self.usuarios:
            usuario.client.send(message)
    


    def criarSala(self, message, usuario):        
        AES_key = self.getKeyFromUser(usuario)

        split_msg = message.split(' ')

        print(split_msg)

        if(len(split_msg) < 3):
            usuario.client.send(encryptAES(encode('ERRO Mensagem falta informações'), AES_key))
            return    

        salaAux = Sala()

        senha = ''
        nome = split_msg[2]
        tipo = split_msg[1]

        if tipo == 'PRIVADA':
            if len(split_msg) < 4:
                usuario.client.send(encryptAES(encode('ERRO Sala privada deve ter senha'), AES_key))
                return
            senha = split_msg[3]   
            salaAux.senha = senha

        if getSala(nome, self.salas) != None:  
            usuario.client.send(encryptAES(encode('ERRO Já existe uma sala com esse nome'), AES_key))
            return

        elif((len(split_msg) > 3 and tipo == 'PUBLICA') or (len(split_msg) > 4 and tipo == 'PRIVADA')):
            usuario.client.send(encryptAES(encode('ERRO Nomes não podem ter espaços'), AES_key))
            return
        
        salaAux.nome = nome
        salaAux.admin = usuario

        self.salas.append(salaAux)

        usuario.client.send(encryptAES(encode('CRIAR_SALA_OK'), AES_key))

    
    def fecharSala(self, message, usuario):
        AES_key = self.getKeyFromUser(usuario)

        split_msg = message.split(' ')
        
        if(len(split_msg) < 2):
            usuario.client.send(encryptAES(encode('ERRO Mensagem falta informações'), AES_key))
            return    

        nomeSala = split_msg[1]
    
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encryptAES(encode('ERRO Sala non ecziste'), AES_key))
            return
        
        if usuario != salaAux.admin:
            usuario.client.send(encryptAES(encode('ERRO Usuário não é admin'), AES_key))
            return

        # removendo a sala do servidor
        index = self.salas.index(salaAux)
        self.salas.pop(index)

        # separando mensagem dos atributos do protocolo
        frase = 'SALA_FECHADA ' + nomeSala
        for usr in salaAux.usuarios:
            usr_AES_key = self.getKeyFromUser(usr)
            usr.client.send(encryptAES(encode(frase), usr_AES_key))




    def banirUsuario(self, message, usuario):
        AES_key = self.getKeyFromUser(usuario)

        split_msg = message.split(' ')

        if(len(split_msg) < 3):
            usuario.client.send(encryptAES(encode('ERRO Mensagem falta informações'), AES_key))
            return

        nomeSala = split_msg[1]
    
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encryptAES(encode('ERRO Sala non ecziste'), AES_key))
            return
        
        if usuario != salaAux.admin:
            usuario.client.send(encryptAES(encode('ERRO Usuário não é admin'), AES_key))
            return


        nomeUsuarioBanido = split_msg[2]
        usuarioBanido = getUsuario(nomeUsuarioBanido, salaAux.usuarios)

        if usuarioBanido == None:
            usuario.client.send(encryptAES(encode('ERRO Usuário a ser banido não está na sala'), AES_key))
            return
        
        if usuarioBanido == usuario:
            usuario.client.send(encryptAES(encode('ERRO Admin não pode se banir'), AES_key))
            return

        index = self.salas.index(salaAux)
        self.salas[index].banidos.append(usuarioBanido)

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.remove(usuarioBanido)

        usuarioBanido.client.send(encryptAES(encode(f'BANIDO_DA_SALA {salaAux.nome}'), usuarioBanido.AES_key))
        usuario.client.send(encryptAES(encode('BANIMENTO_OK'), AES_key))

        for usr in salaAux.usuarios:
            usr_AES_key = self.getKeyFromUser(usr)
            usr.client.send(encryptAES(encode(f'SAIU {salaAux.nome} {usuarioBanido.nome}'), usr_AES_key))  

    


    def entrarSala(self, message, usuario):
        AES_key = self.getKeyFromUser(usuario)

        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encryptAES(encode('ERRO Mensagem falta informações'), AES_key))
            return    
        
        senha = ''
        nomeSala = split_msg[1]

        if((len(split_msg) > 3)):
            usuario.client.send(encryptAES(encode('ERRO Muitos argumentos na mensagem'), AES_key))
            return
        
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encryptAES(encode('ERRO Sala não existe'), AES_key))
            return

        if usuario in salaAux.banidos:
            usuario.client.send(encryptAES(encode('ERRO Usuário foi banido da sala'), AES_key))
            return

        if usuario in salaAux.usuarios:
            usuario.client.send(encryptAES(encode('ERRO Usuário já está na sala'), AES_key))
            return

        print(message)
        if((len(split_msg) == 3)):
            senha = split_msg[2]

        if(salaAux.senha != '') and (salaAux.senha != senha):
            usuario.client.send(encryptAES(encode('ERRO Senha incorreta'), AES_key))
            return

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.append(usuario)


        mensagem = 'ENTRAR_SALA_OK'
        
        for usr in salaAux.usuarios:
            mensagem = mensagem + ' ' + usr.nome
        usuario.client.send(encryptAES(encode(mensagem), AES_key))



    def sairSala(self, message, usuario):
        AES_key = self.getKeyFromUser(usuario)

        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encryptAES(encode('ERRO Mensagem falta informações'), AES_key))
            return    
        
        nomeSala = split_msg[1]

        if((len(split_msg) > 2)):
            usuario.client.send(encryptAES(encode('ERRO Muitos argumentos na mensagem'), AES_key))
            return
        
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encryptAES(encode('ERRO Sala não existe'), AES_key))
            return

        if not(usuario in salaAux.usuarios):
            usuario.client.send(encryptAES(encode('ERRO Usuário não está na sala'), AES_key))
            return

        index = self.salas.index(salaAux)
        self.salas[index].usuarios.remove(usuario)

        
        usuario.client.send(encryptAES(encode('SAIR_SALA_OK'), AES_key))

        for usr in salaAux.usuarios:
            usr_AES_key = self.getKeyFromUser(usr)
            usr.client.send(encryptAES(encode(f'SAIU {salaAux.nome} {usuario.nome}'), usr_AES_key))  



    def listarSalas(self, usuario):
        AES_key = self.getKeyFromUser(usuario)

        mensagem = 'SALAS'

        for sala in self.salas:
            mensagem = mensagem + ' ' + sala.nome
            if sala.senha == '':
                mensagem = mensagem + '[publica]'
            else:
                mensagem = mensagem + '[privada]'
        
        usuario.client.send(encryptAES(encode(mensagem), AES_key))



    def enviarMensagem(self, message, usuario):
        AES_key = self.getKeyFromUser(usuario)

        split_msg = message.split(' ')

        if(len(split_msg) < 2):
            usuario.client.send(encryptAES(encode('ERRO Mensagem falta informações'), AES_key))
            return   

        nomeSala = split_msg[1]
        salaAux = getSala(nomeSala, self.salas)
        if(salaAux == None):
            usuario.client.send(encryptAES(encode('ERRO Sala não existe'), AES_key))
            return

        if getUsuario(usuario.nome, salaAux.usuarios) == None:
            usuario.client.send(encryptAES(encode('ERRO Usuário não faz parte da sala'), AES_key))
            return

        # separando mensagem dos atributos do protocolo
        palavras = split_msg[2:]
        frase = f'MENSAGEM {nomeSala} {usuario.nome} '
        frase = frase + ' '.join(palavras) if palavras else ''

        for usr in salaAux.usuarios:
            usr_AES_key = self.getKeyFromUser(usr)
            usr.client.send(encryptAES(encode(frase), usr_AES_key))  
        
    
    def getKeyFromUser(self, usuario):
        index = self.usuarios.index(usuario)
        return self.usuarios[index].AES_key


    def treat_message(self, message, usuario):
        print("1") 

        print("2")
        try:
            authMessage = decode(message)
            split_msg = authMessage.split(' ') # separa a mensagem de acordo com espacos
        except:
            split_msg = 'non', 'funfa'
        
        command = split_msg[0]

        print("3")
        if command == 'AUTENTICACAO':
            print("autenticar usuario")
            self.autenticarUsuario(authMessage, usuario)
            print('3.5')
            return  

        
        print(message)
        print(type(message))
        AES_key = self.getKeyFromUser(usuario)
        
        if AES_key == b'':
            usuario.client.send(encode('ERRO Usuário não foi autenticado'))
            return
        
        message = decryptAES(message, AES_key)
        message = decode(message)
        print(message)
        print(type(message))

        #print(message)

        split_msg = message.split(' ')
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
                self.sairSala(message, usuario)
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
                message = usuario.client.recv(1024)
                self.treat_message(message, usuario)
                #self.broadcast(message)
            except:
                index = self.usuarios.index(usuario)
                nome = self.usuarios[index].nome
                self.usuarios.remove(usuario)
                usuario.client.close()
                #self.broadcast(encode(f'{nome} saiu do chat!'))
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
                #print(split_msg)
                #print(nome,'res')
                
                
                if getUsuario(nome, self.usuarios) != None:
                    client.send(encode("ERRO Já existe um usuário com esse nome")) 
                    #return

                elif(len(split_msg) > 2):
                    client.send(encode("ERRO Nomes não podem ter espaços"))
                    #return

                else:     
                    usuario = Usuario(client)
                    usuario.nome = nome
                    
                    self.usuarios.append(usuario)

                    #print(f"nome do cliente é {nome}!")
                    #self.broadcast(encode(f"{nome} entrou no chat!"))
                    client.send(encode('REGISTRO_OK'))
                    #print("regok")
                    thread = threading.Thread(target=self.handle, args=(usuario,))
                    thread.start()

                    client.send(encode('REGISTRO_OK'))


if __name__ == "__main__":
    get_host_ip()
    servidor = Servidor()
    servidor.register()

    servidor.server.close()