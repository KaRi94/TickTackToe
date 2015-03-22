from client.client import *
from server.server import *

select = int(input('You want start server(0) or client(1): '))
if select == 0:
    print('Server starts')
    server = MyTCPServer(('127.0.0.1', 13373), MyTCPServerHandler)
    server.serve_forever()
elif select == 1:
    server = input('Server IP: ')
    port = int(input('Port: '))
    c = Client(server, port)
    c.run()