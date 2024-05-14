import os
import socket
import threading
import base64

from Crypto.PublicKey import RSA  # provided by pycryptodome
from Crypto.Cipher import PKCS1_OAEP
import binascii

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
            message = decode(client.recv(1024))
            print(message)
        except:
            print("Erro!")
            client.close()
            break


def write():
    while True:
        message = input("")
        client.send(encode(message))


def autenticarUsuario(username):
    # requisitando autenticação
    client.send(encode(f'AUTENTICADAO {username}')) 
    
    resposta = decode(client.recv(1024)) # resposta do server
    split_res = resposta.split(' ')
    
    while(split_res[0] != 'CHAVE_PUBLICA'):
        resposta = decode(client.recv(1024))
        split_res = resposta.split(' ')

    _, public_key_str = resposta.split(' ', 1)


    # criptografando a chave AES com a chave publica
    AES_key = get_random_bytes(32)  # Generating keys/passphrase
    print(AES_key)
    
    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(public_key_str))
    encrypted_AES_key = cipher_rsa.encrypt(AES_key)

    #client.send(encode(f'CHAVE_SIMETRICA {encrypted_AES_key}')) 
    client.send(encode(f'CHAVE_SIMETRICA {encrypted_AES_key}')) 

    hold = input("Holding")
    
    #


    """ 
    split_res = resposta.split(' ')
    if (split_res[0] == 'ERRO'):
        print(resposta)
        return

    public_key = split_res[1] # recuperando a chave publica da resposta

    AES_key = get_random_bytes(32) # gerando chave AES

    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(public_key))
    encrypted_data = cipher_rsa.encrypt(AES_key) # criptografando chave AES com chave publica

    client.send(f'CHAVE_SIMETRICA {encode(encrypted_data)}') # enviando chave AES para o servidor

    print(AES_key)
     """


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
            

ip = input("Digite o IP do server: ")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((str(ip), 12345))

username = input("Digite o seu username: ")
registro()
autenticarUsuario(username)

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()





