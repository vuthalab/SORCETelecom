import socket

HOST = ''
PORT = 6666
s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST,PORT))

messagebank = ["Temp?","Temp42.132113","Loc?","Temp123","temp?","Alt?","Humid?", "Loc?","Temp23","Temp13.32","Ping","Temp?","Alt?","Pong?","Hrlp","Temp13"]



for i in range(0,len(messagebank),1):
    print("-------------------------------------------------------")
    message = messagebank[i]
    s.sendall(message.encode())
    data= (s.recv(1024)).decode()
    print("Message Sent:", message)
    print("Received Data is:",data)
    print("-------------------------------------------------------")

print("Done")
s.close()

