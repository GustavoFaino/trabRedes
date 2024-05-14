import os
import socket
import threading
import base64
import hashlib


from Crypto.PublicKey import RSA  # provided by pycryptodome
from Crypto.Cipher import PKCS1_OAEP

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes


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
    while True:
        try:
            message = decryptAES(client.recv(1024), AES_key)
            message = decode(message)
            print(message)
        except:
            print("Erro!")
            client.close()
            break


def write():
    while True:
        message = input("")
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
            return
        elif(split_res[0] == 'ERRO'):
            print(response)
            break


""" def createChat():
    print("create")
    c = input()
    
# joinChat:


def menu():
    choice = 'a'

    while choice != '0':

        print("[0] Sair")
        print("[1] Entrar Sala")
        print("[2] Criar em Sala")

        choice = input()

        match choice:
            case '1':
                print("entrar sala")
            case '2':
                createChat()
        clear() """
            

# LEIA-ME
# quando for fazer a UI use hashed_data = hashlib.sha256(data.encode()) pra passar as senhas no criar e entrar sala

ip = input("Digite o IP do server: ")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((str(ip), 12345))

username = input("Digite o seu username: ")
registro()
AES_key = get_random_bytes(32)  # Generating keys/passphrase

autenticarUsuario(username, AES_key)
receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()





