import socket
import threading

def receive():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message == 'NICK':
                client.send(nickname.encode('utf-8'))
            else:
                print(message)
        except:
            print("Erro!")
            client.close()
            break

def write():
    while True:
        message = f'{nickname}: {input("")}'
        client.send(message.encode('utf-8'))



ip = input("Digite o IP do server: ")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((str(ip), 12345))

nickname = input("Digite o seu nickname: ")



receive_thread = threading.Thread(target=receive)
receive_thread.start()

write_thread = threading.Thread(target=write)
write_thread.start()

