import os
import socket
import threading

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            print(message)
        except:
            print("Erro!")
            client.close()
            break


def write():
    while True:
        message = input("")
        client.send(message.encode('utf-8'))


def registro():
    message = f'REGISTRO {username}'
    client.send(message.encode('utf-8'))

    while True:
        response = client.recv(1024).decode('utf-8') # cuidar esta linha 
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





