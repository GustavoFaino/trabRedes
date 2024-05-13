import os
import socket
import threading
import base64


def encode(msg):
    return base64.b64encode(msg.encode('utf-8'))

def decode(msg):
    return (base64.b64decode(msg).decode('utf-8'))


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

receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()





