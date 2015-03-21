from abc import ABCMeta
import random
import socketserver
import json
import string

class MyTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class MyTCPServerHandler(socketserver.BaseRequestHandler):
    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    game = {}
    def handle(self):
        try:
            data = json.loads(self.request.recv(1024).decode('UTF-8').strip())
            # print(data['message'])
            if data['message'] == 'start':
                game_id = ''.join(random.sample(MyTCPServerHandler.chars, 20))
                data = {
                    'message': 'ok_give_name',
                    'game_id': game_id,
                }
                self.request.sendall(bytes(json.dumps(data), 'UTF-8'))
                MyTCPServerHandler.game[game_id] = Game(self, game_id)
            if data['message'] == 'name':
                game_id = data['game_id']
                name = data['name']
                game = MyTCPServerHandler.game[game_id]
                response = game.register_player(name)
                data = {
                    'message': 'ok_start_game',
                    'game_id': game_id,
                    'response': response,
                }
                self.request.sendall(bytes(json.dumps(data), 'UTF-8'))
            if data['message'] == 'turn':
                game_id = data['game_id']
                area = data['area']
                marker = data['marker']
                game = MyTCPServerHandler.game[game_id]
                response = game.turn(area, marker)
                if response['status'] == 'gameover':
                    data = {
                        'message': 'gameover',
                        'game_id': game_id,
                        'response': response,
                    }
                else:
                    data = {
                        'message': 'your_turn',
                        'game_id': game_id,
                        'response': response,
                    }
                self.request.sendall(bytes(json.dumps(data), 'UTF-8'))
        except Exception as e:
            pass

    def send_message(self, data):
        try:
            self.request.sendall(bytes(json.dumps(data), 'UTF-8'))
        except:
            pass

class Board(object):

    def __init__(self):
        # create empty board
        self.board = [None] * 9
        self.winning_combos = (
            # horizontal combos
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            # vertical combos
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            # diagonal combos
            [0, 4, 8], [2, 4, 6],
        )

    def display_board(self):
        board = [' ' if x is None else x for x in self.board]
        board_to_display = Board.board_form % tuple(board)
        return board_to_display

    def is_free(self, index):
        return not self.board[index]

    def put_marker_in_area(self, area, marker):
        self.board[area] = marker

class Player(object):
    __metaclass__ = ABCMeta

    def __init__(self, name, marker):
        self.player_name = name
        self.marker = marker


class HumanPlayer(Player):
    def get_move(self, board):
        pass
        # area = int(input('Type empty area where you want to place %s (0-8): ' % self.marker))
        # while True:
        #     if 0 <= area <= 8 and board.is_free(area):
        #         return area
        #     area = int(input('Wrong choice!, Try again (0-8): '))


class ComputerPlayer(Player):
    def get_move(self, board):
        indexes = [index for (index, value) in enumerate(board) if value is None]
        index = random.choice(indexes)
        board[index] = self.marker


class Game(object):
    def __init__(self, server, game_id):
        self.server = server
        self.game_id = game_id
        self.board = Board()
        self.markers = self.draw_marker()

    def register_player(self, name):
        computer_name = 'ComputerBot'
        self.first_player = HumanPlayer(name=name, marker=self.markers[0])
        self.second_player = ComputerPlayer(name=computer_name, marker=self.markers[1])
        self.players = (self.first_player, self.second_player)
        whose_turn = random.choice(self.players)
        if whose_turn == self.second_player:
            self.second_player.get_move(self.board.board)
        data = {
            'text': '%s vs %s - %s starts' % (name, computer_name, whose_turn.player_name),
            'marker': self.first_player.marker,
            'board': self.board.board,
            'status': True,
        }
        return data

    def turn(self, area, marker):
        result = False
        gameover = False
        if 1 <= area <= 9 and self.board.is_free(area-1):
            self.board.put_marker_in_area(area-1, marker)
            result = True
        data = {
            'status': result,
            'board': self.board.board,
        }
        if result:
            if self.is_winner(marker):
                data['status'] = 'gameover'
                data['reason'] = 'win'
                gameover = True
            if self.is_draw():
                data['status'] = 'gameover'
                data['reason'] = 'draw'
                gameover = True
            if not gameover:
                self.second_player.get_move(self.board.board)
            if self.is_winner(self.second_player.marker):
                data['status'] = 'gameover'
                data['reason'] = 'lose'
                gameover = True
            if self.is_draw():
                data['status'] = 'gameover'
                data['reason'] = 'draw'
                gameover = True
        return data

    def is_draw(self):
        if all(self.board.board):
            return True

    def is_winner(self, marker):
        for combo in self.board.winning_combos:
            if self.board.board[combo[0]] == self.board.board[combo[1]] == self.board.board[combo[2]] == marker:
                return True
        return False

    def draw_marker(self):
        markers = ('X', 'O')
        return random.sample(markers, 2)


server = MyTCPServer(('127.0.0.1', 13373), MyTCPServerHandler)
server.serve_forever()