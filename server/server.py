from abc import ABCMeta
import random
import socketserver
import json
import string
from copy import deepcopy
import logging

logging.basicConfig(
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m/%d/%Y %I:%M:%S %p',
    filename='logs.log',
    level=logging.DEBUG
)
logger_ServerConnection = logging.getLogger('ServerConnection')
logger_ServerGame = logging.getLogger('ServerGame')

class MyTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

class MyTCPServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = json.loads(self.request.recv(1024).decode('UTF-8').strip())
            message = data.get('message')
            if message:
                logger_ServerConnection.info('Server received %s message' % message)
            if message == 'start':
                game_id = ''.join(random.sample(Game.chars, 20))
                data = {
                    'message': 'ok_give_name',
                    'game_id': game_id,
                }
                self.send_message(data)
                Game.game[game_id] = Game(game_id)
            if message == 'name':
                game_id = data['game_id']
                name = data['name']
                game = Game.game.get(game_id)
                if game:
                    response = game.register_player(name)
                    data = {
                        'message': 'ok_start_game',
                        'game_id': game_id,
                        'response': response,
                    }
                    self.send_message(data)
            if message == 'turn':
                game_id = data.get('game_id')
                area = data.get('area')
                marker = data.get('marker')
                game = Game.game.get(game_id)
                if game:
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
                    self.send_message(data)
        except Exception as e:
            logger_ServerConnection.exception(e)

    def send_message(self, data):
        try:
            self.request.sendall(bytes(json.dumps(data), 'UTF-8'))
            logger_ServerConnection.info('Server sent %s message' % data.get('message'))
        except Exception as e:
            logger_ServerConnection.exception(e)

class Board(object):
    winning_combos = (
            # horizontal combos
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            # vertical combos
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            # diagonal combos
            [0, 4, 8], [2, 4, 6],
    )
    def __init__(self):
        # create empty board
        self.board = [None] * 9

    def get_free_corners(self):
            return [index for (index, val) in enumerate(self.board) if self.is_free(index) and index in [0, 2, 6, 8]]

    def get_free_center(self):
        return [4] if self.is_free(4) else []

    def is_free(self, index):
        return not self.board[index]

    def put_marker_in_area(self, area, marker):
        try:
            self.board[area] = marker
        except Exception as e:
            logger_ServerGame.exception(e)
            raise ValueError('area value should be between 0 and 8')

class Player(object):
    markers = ('X', 'O')
    __metaclass__ = ABCMeta

    def __init__(self, name, marker):
        self.player_name = name
        self.marker = marker

    @classmethod
    def is_winner(cls, board_obj, marker):
        for combo in Board.winning_combos:
            if board_obj.board[combo[0]] == board_obj.board[combo[1]] == board_obj.board[combo[2]] == marker:
                return True
        return False

    def get_opponent_marker(self):
        return [x for x in Player.markers if x != self.marker][0]

class HumanPlayer(Player):
    # For now unused
    def get_move(self, board):
        pass
        # area = int(input('Type empty area where you want to place %s (0-8): ' % self.marker))
        # while True:
        #     if 0 <= area <= 8 and board.is_free(area):
        #         return area
        #     area = int(input('Wrong choice!, Try again (0-8): '))


class ComputerPlayer(Player):
    def get_move(self, board_obj):
        logger_ServerGame.info('Computer makes move')
        indexes = [index for (index, value) in enumerate(board_obj.board) if value is None]

        # Check if the computer can win in the next move
        for index in indexes:
            copy_board = deepcopy(board_obj)
            if copy_board.is_free(index):
                copy_board.board[index] = self.marker
                if Player.is_winner(copy_board, self.marker):
                    board_obj.board[index] = self.marker
                    return

        # Check if the player could win on their next move, and block them.
        opponent_marker = self.get_opponent_marker()
        for index in indexes:
            copy_board = deepcopy(board_obj)
            if copy_board.is_free(index):
                copy_board.board[index] = opponent_marker
                if Player.is_winner(copy_board, opponent_marker):
                    board_obj.board[index] = self.marker
                    return

        corners = board_obj.get_free_corners()
        if corners:
            index = random.choice(corners)
            board_obj.board[index] = self.marker
            return

        center = board_obj.get_free_center()
        if center:
            index = random.choice(center)
            board_obj.board[index] = self.marker
            return

        index = random.choice(indexes)
        board_obj.board[index] = self.marker


class Game(object):
    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    game = {}

    def __init__(self, game_id):
        self.game_id = game_id
        self.board = Board()
        self.markers = self.draw_marker()

    def register_player(self, name):
        computer_name = 'ComputerBot'
        self.first_player = HumanPlayer(name=name, marker=self.markers[0])
        self.second_player = ComputerPlayer(name=computer_name, marker=self.markers[1])
        self.players = (self.first_player, self.second_player)
        whose_turn = self.draw_first_player(self.players)
        if whose_turn == self.second_player:
            self.second_player.get_move(self.board)
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
            if Player.is_winner(self.board, marker):
                data['status'] = 'gameover'
                data['reason'] = 'win'
                gameover = True
            if self.is_draw():
                data['status'] = 'gameover'
                data['reason'] = 'draw'
                gameover = True
            if not gameover:
                self.second_player.get_move(self.board)
                if Player.is_winner(self.board, self.second_player.marker):
                    data['status'] = 'gameover'
                    data['reason'] = 'lose'
                if self.is_draw():
                    data['status'] = 'gameover'
                    data['reason'] = 'draw'
        return data

    def draw_first_player(self, players):
         return random.choice(players)

    def is_draw(self):
        if all(self.board.board):
            return True

    def draw_marker(self):
        return random.sample(Player.markers, 2)