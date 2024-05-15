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

# variável de shutdown do lado do cliente
shutdownFlag = False



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


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


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
        elif(split_res[0] == 'ERRO'):
            print(response)
            break



def menu():
    choice = 'a'

    while choice != '0':

        print("[0] Sair")
        print("[1] Criar Sala")
        print("[2] Entrar em sala")

        choice = input()

        match choice:
            case '1':
                print("Listar Comandos")
            case '2':
                print("Enviar Comando")
                #createChat()
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


write_thread = threading.Thread(target=write)
write_thread.start()

receive_thread = threading.Thread(target=receive)
receive_thread.start()

while not shutdownFlag: 
    pass # não faz nada

print("Programa finalizado")
write_thread.join()
receive_thread.join()


