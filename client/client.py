import socket
import json

class Connection(object):
    def __init__(self, IP, PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((IP, PORT))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.socket.close()

    def send_message(self, data):
        # print(data)
        self.socket.send(bytes(json.dumps(data), 'UTF-8'))

    def retrieve_message(self):
        result = json.loads(self.socket.recv(1024).decode('UTF-8'))
        # print(result)
        return result

class Interface(object):
    board_form = '''
        | %s | %s | %s |
        -------------
        | %s | %s | %s |
        -------------
        | %s | %s | %s |
        '''

    def __init__(self):
        print('Welcome to Tic Tac Toe game.')

    def display_board(self, board):
        board = [' ' if x is None else x for x in board]
        print(Interface.board_form % tuple(board))

class Client(object):
    def __init__(self):
        self.interface = Interface()

    def run(self):
        with Connection('127.0.0.1', 13373) as connection:
            print('Calling server')
            data = {
                'message': 'start',
            }
            connection.send_message(data)
            result = connection.retrieve_message()

        with Connection('127.0.0.1', 13373) as connection:
            if result['message'] == 'ok_give_name':
                game_id = result['game_id']
                name = input('Type your name: ')
                data = {
                    'message': 'name',
                    'game_id': game_id,
                    'name': name,
                }
                connection.send_message(data)
                result = connection.retrieve_message()
            else:
                print('Server problem occurred. Try again.')

            if result['message'] == 'ok_start_game':
                response = result['response']
                text = response['text']
                marker = response['marker']
                print(text)
            else:
                print('Server problem occurred. Try again.')

        # with Connection('127.0.0.1', 13373) as connection:
        while True:
            response_game_id = result.get('game_id')
            if result and response_game_id != game_id:
                print('dupa')
                continue
            response = result['response']

            if result['message'] == 'gameover':
                board = response['board']
                reason = response.get('reason')
                self.interface.display_board(board)
                if reason == 'win':
                    print('You WIN!')
                elif reason == 'lose':
                    print('You LOSE!')
                if reason == 'draw':
                    print('DRAW!')
                print('Game over.')
                break

            status = response['status']
            if status:
                board = response['board']
                self.interface.display_board(board)
                area = int(input('Now your move. Type empty area where you want to place %s (1-9): ' % marker))
            else:
                area = int(input('Wrong choice!, Try again (1-9): '))
            data = {
                'message': 'turn',
                'game_id': game_id,
                'area': area,
                'marker': marker,
            }
            with Connection('127.0.0.1', 13373) as connection:
                connection.send_message(data)
                result = connection.retrieve_message()



            # result = connection.retrieve_message()
            # result = connection.retrieve_message()
            # if result['message'] == 'ok':
            #     print(result)

c = Client()
c.run()