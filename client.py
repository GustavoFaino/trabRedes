import os
import sys
import socket
import threading
import base64
import hashlib

from Crypto.PublicKey import RSA  # provided by pycryptodome
from Crypto.Cipher import PKCS1_OAEP

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

import getpass


# variável de shutdown do lado do cliente
shutdownFlag = False
serverMessage = ''


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')



def encode(msg):
    return base64.b64encode(msg.encode('utf-8'))

def decode(msg):
    return (base64.b64decode(msg).decode('utf-8'))


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


def receive():
    global shutdownFlag
    while not shutdownFlag:
        
        try:
            message = client.recv(1024)
            message = decryptAES(message, AES_key)
            message = decode(message)
            print(message)
        except:
            print("Conexão Perdida!")
            client.close()
            shutdownFlag = True
            


def write():
    while True:
        message = input("")
        
        if shutdownFlag:
            break

        split_msg = message.split(' ')

        if(len(split_msg)):
            if(split_msg[0] == 'CRIAR_SALA') and (split_msg[1] == 'PRIVADA') and (len(split_msg) == 4): # caso tente criar uma sala e esteja passando uma senha, faça o hash da senha
                senha = split_msg[3]
                split_msg[3] = hashlib.sha256(senha.encode()).hexdigest()
                message = ' '.join(split_msg)

            elif(split_msg[0] == 'ENTRAR_SALA') and (len(split_msg) == 3): # caso tente entrar em uma sala e esteja passando uma senha, faça o hash da senha
                senha = split_msg[2]
                split_msg[2] = hashlib.sha256(senha.encode()).hexdigest()
                message = ' '.join(split_msg)

        client.send(encryptAES(encode(message), AES_key))


sairFlag = False


def sairSala(sala):
    client.send(encryptAES(encode(f'SAIR_SALA {sala}'), AES_key))
    #global sairFlag
    #sairFlag = False


def enviarMensagem(sala):
    global sairFlag
    while True:
                
        mensagem = input()
        if(mensagem == 'SAIR_SALA'):
            sairSala(sala)
            sairFlag = True
            return
        
        elif sairFlag:
            sairSala(sala)
            return

        split_msg = mensagem.split(' ')
        
        if(split_msg[0] == 'BANIR_USUARIO' and len(split_msg) == 2):
            client.send(encryptAES(encode(f'BANIR_USUARIO {sala} {split_msg[1]}'), AES_key)) 

        elif(split_msg[0] == 'FECHAR_SALA'):
            client.send(encryptAES(encode(f'FECHAR_SALA {sala}'), AES_key))
        else:
            client.send(encryptAES(encode(f'ENVIAR_MENSAGEM {sala} {mensagem}'), AES_key))  



def receberMensagem():
    global serverMessage 
    global sairFlag

    while True:                
        try:
            serverMessage = decode(decryptAES(client.recv(1024), AES_key))
        except:
            print("ERRO Conexão perdida")
            sairFlag = True
            return

        if sairFlag == True:
            return

        split_srv = serverMessage.split(' ')
        command = split_srv[0]
        
        match command:
            case 'MENSAGEM':
                if(split_srv[2] != username):
                    string = ' '.join(split_srv[3:])
                    print(f'{split_srv[2]}: {string}')
            
            case 'BANIDO_DA_SALA' | 'SALA_FECHADA':
                print(serverMessage)
                sairFlag = True
                print(decode(decryptAES(client.recv(1024), AES_key)))
                return

            case _:
                print(serverMessage)

        



def autenticarUsuario(username, AES_key):
    # requisitando autenticação
    client.send(encode(f'AUTENTICACAO {username}')) 
    
    resposta = decode(client.recv(1024)) # resposta do server
    split_res = resposta.split(' ')
    
    while(split_res[0] != 'CHAVE_PUBLICA'):
        resposta = decode(client.recv(1024))
        split_res = resposta.split(' ')

    _, public_key_str = resposta.split(' ', 1)


    # criptografando a chave AES com a chave publica
    #print(AES_key)
    
    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(public_key_str))
    encrypted_AES_key = cipher_rsa.encrypt(AES_key)

    #client.send(encode(f'CHAVE_SIMETRICA {encrypted_AES_key}')) 
    client.send(encode(f'CHAVE_SIMETRICA {encrypted_AES_key}')) 

    print("Autenticação Bem Sucedida ")
    #hold = input("Holding")
    


def registro():
    message = f'REGISTRO {username}'
    client.send(encode(message))

    while True:
        response = decode(client.recv(1024)) # cuidar esta linha 
        split_res = response.split(' ')
        

        if(split_res[0] == 'REGISTRO_OK'):
            print("Registro feito com sucesso!")
            return
        elif(split_res[0] == 'ERRO'):
            print(response)
            sys.exit(1)


def criarSala():
    
    clear()
    # Criando a sala
    nome = input("Nome da sala: ")
    senha = getpass.getpass(prompt="Crie uma senha: ")
    senha = hashlib.sha256(senha.encode()).hexdigest()

    if(senha == ''):
        message = f'CRIAR_SALA PUBLICA {nome}'
    else:
        message = f'CRIAR_SALA PRIVADA {nome} {senha}'

    client.send(encryptAES(encode(message), AES_key))
    
    resposta = decode(decryptAES(client.recv(1024), AES_key))
    print(resposta)
    input("[Pressione Enter]")



def entrarSala():
    clear()

    client.send(encryptAES(encode('LISTAR_SALAS'), AES_key))
    msgSalas = decode(decryptAES(client.recv(1024), AES_key))
    split_msg = msgSalas.split(' ')
    split_msg = split_msg[1:]

    print("Salas Disponíveis:")
    for s in split_msg:
        print(f'- {s} ')


    nome = input("Nome da sala: ")
    senha = getpass.getpass(prompt="Senha da sala: ")
    senha = hashlib.sha256(senha.encode()).hexdigest()
    
    if(senha == ''):
        message = f'ENTRAR_SALA {nome}'
    else:
        message = f'ENTRAR_SALA {nome} {senha}'

    client.send(encryptAES(encode(message), AES_key))

    resposta = decode(decryptAES(client.recv(1024), AES_key))
    print(resposta)

    split_res = resposta.split(' ')
    if(split_res[0] == 'ERRO'):
        input("[Pressione Enter]")
        return
    
    print("Para sair da sala escreva: SAIR_SALA")
    print("Para fechar a sala escreva: FECHAR_SALA")
    print("Para banir um usuário escreva: BANIR_USUARIO <nome>")
    input("[Pressione Enter]")
    clear()

    enviarMensagem_thread = threading.Thread(target=enviarMensagem, args=(nome,))
    enviarMensagem_thread.start()

    receberMensagem_thread = threading.Thread(target=receberMensagem)
    receberMensagem_thread.start()

    enviarMensagem_thread.join()
    receberMensagem_thread.join()
    
    global sairFlag
    sairFlag = False
    
    input("[Pressione Enter]")



def menu():
    choice = 'a'
    while choice != '0':

        print("[0] Sair")
        print("[1] Criar Sala")
        print("[2] Entrar em sala")

        choice = input()

        match choice:
            case '1':
                print("criar sala")
                criarSala()
            case '2':
                print("entrarsala")
                entrarSala()
        clear()
            

ip = input("Digite o IP do server: ")
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((str(ip), 12345))
except socket.error as e:
    print(f"Erro na conexão: {e}")
    sys.exit(1)

username = input("Digite o seu username: ")
registro()

AES_key = get_random_bytes(32)  # Generating keys/passphrase
autenticarUsuario(username, AES_key)



# menu do usuário
menu()


""" write_thread = threading.Thread(target=write)
write_thread.start()

receive_thread = threading.Thread(target=receive)
receive_thread.start()

while not shutdownFlag: 
    pass # não faz nada """

print("Programa finalizado")
#write_thread.join()
#receive_thread.join()


