from unittest import TestCase, mock
from server.server import Board, HumanPlayer, Player, ComputerPlayer, Game


class BoardTest(TestCase):
    def setUp(self):
        self.board = Board()

    def test_object_initialize(self):
        for area in self.board.board:
            self.assertIsNone(area)

    def test_get_free_corners(self):
        self.assertListEqual([0, 2, 6, 8], self.board.get_free_corners())

        # Set one corner to X
        self.board.board[0] = 'X'
        self.assertListEqual([2, 6, 8], self.board.get_free_corners())

    def test_get_free_center(self):
        self.assertListEqual([4], self.board.get_free_center())

        self.board.board[4] = 'O'
        self.assertListEqual([], self.board.get_free_center())

    def test_is_free(self):
        self.assertTrue(self.board.is_free(3))
        self.board.board[3] = 'X'
        self.assertFalse(self.board.is_free(3))

        self.assertTrue(self.board.is_free(8))
        self.board.board[8] = 'O'
        self.assertFalse(self.board.is_free(8))

    def test_put_marker_in_area(self):
        self.assertTrue(self.board.is_free(3))
        self.board.put_marker_in_area(3, 'X')
        self.assertFalse(self.board.is_free(3))
        self.assertEqual('X', self.board.board[3])

        self.assertTrue(self.board.is_free(8))
        self.board.put_marker_in_area(8, 'X')
        self.assertFalse(self.board.is_free(8))
        self.assertEqual('X', self.board.board[8])

    def test_put_marker_in_area_throw_exception(self):
        with self.assertRaises(ValueError):
            self.board.put_marker_in_area(10, 'X')


class HumanPlayerTest(TestCase):
    def setUp(self):
        self.playerX = HumanPlayer(name='testX', marker='X')
        self.playerO = HumanPlayer(name='testO', marker='O')

    def test_object_initialize(self):
        self.assertEqual('testX', self.playerX.player_name)
        self.assertEqual('testO', self.playerO.player_name)

        self.assertEqual('X', self.playerX.marker)
        self.assertEqual('O', self.playerO.marker)

    def test_is_winner(self):
        winning_combos = Board.winning_combos
        board = Board()
        self.assertFalse(Player.is_winner(board, self.playerX.marker))
        board.board[0] = 'X'
        board.board[1] = 'X'
        board.board[2] = 'X'
        self.assertTrue(Player.is_winner(board, self.playerX.marker))
        self.assertFalse(Player.is_winner(board, self.playerO.marker))

    def test_get_opponent_marker(self):
        self.assertEqual('O', self.playerX.get_opponent_marker())
        self.assertEqual('X', self.playerO.get_opponent_marker())


class ComputerPlayerTest(TestCase):
    def setUp(self):
        self.player = HumanPlayer(name='test', marker='O')
        self.comp_player = ComputerPlayer(name='Bot', marker='X')
        self.board = Board()

    def test_get_move_computer_select_and_win(self):
        self.board.board[0] = self.comp_player.marker
        self.board.board[2] = self.comp_player.marker
        self.comp_player.get_move(self.board)
        self.assertEqual(self.comp_player.marker, self.board.board[1])

    def test_get_move_computer_defend_itself(self):
        self.board.board[0] = self.player.marker
        self.board.board[2] = self.player.marker
        self.comp_player.get_move(self.board)
        self.assertEqual(self.comp_player.marker, self.board.board[1])

    def test_get_move_computer_prefer_corners(self):
        self.comp_player.get_move(self.board)
        self.assertIn(
            self.comp_player.marker,
            [self.board.board[0], self.board.board[2], self.board.board[6], self.board.board[8]]
        )


class GameTest(TestCase):
    def setUp(self):
        self.game = Game('testid')

    def test_object_initialize(self):
        self.assertEqual('testid', self.game.game_id)
        self.assertTrue(isinstance(self.game.board, Board))

    @mock.patch.object(ComputerPlayer, 'get_move')
    @mock.patch.object(Game, 'draw_first_player')
    def test_register_player(self, draw_first_player, get_move):
        response = self.game.register_player(name='test')
        draw_first_player.return_value = self.game.first_player
        players = self.game.players
        expected_response = {
            'text': '%s vs %s - %s starts' % (players[0].player_name, players[1].player_name, self.game.first_player.player_name),
            'marker': players[0].marker,
            'board': self.game.board.board,
            'status': True,
        }
        self.assertEqual(0, get_move.call_count)
        # self.assertEqual(expected_response, response)
        self.assertEqual(expected_response['marker'], response['marker'])
        self.assertEqual(expected_response['board'], response['board'])
        self.assertEqual(expected_response['status'], response['status'])

        draw_first_player.return_value = self.game.second_player
        expected_response = {
            'text': '%s vs %s - %s starts' % (players[0].player_name, players[1].player_name, self.game.second_player.player_name),
            'marker': players[0].marker,
            'board': self.game.board.board,
            'status': True,
        }
        # self.assertEqual(expected_response, response)
        self.assertEqual(expected_response['marker'], response['marker'])
        self.assertEqual(expected_response['board'], response['board'])
        self.assertEqual(expected_response['status'], response['status'])

    @mock.patch.object(Board, 'is_free')
    def test_turn_returns_false_if_incorrect_area(self, is_free):
        is_free.return_value = True
        response = self.game.turn(10, 'X')
        self.assertEqual(False, response['status'])
        is_free.return_value = False
        response = self.game.turn(3, 'X')
        self.assertEqual(False, response['status'])


    @mock.patch.object(Board, 'put_marker_in_area')
    @mock.patch.object(Board, 'is_free')
    @mock.patch.object(Player, 'is_winner')
    @mock.patch.object(Game, 'is_draw')
    def test_turn_check_if_game_is_over(self, is_draw, is_winner, is_free, put_marker_in_area):
        is_free.return_value = True
        is_draw.return_value = True
        response = self.game.turn(3, 'X')
        put_marker_in_area.assert_called_once_with(2, 'X')
        self.assertEqual(1, is_draw.call_count)
        self.assertEqual(1, is_winner.call_count)

    @mock.patch.object(ComputerPlayer, 'get_move')
    @mock.patch.object(Board, 'is_free')
    @mock.patch.object(Player, 'is_winner')
    @mock.patch.object(Game, 'is_draw')
    def test_turn_returns_correct_response(self, is_draw, is_winner, is_free, get_move):
        is_free.return_value = True
        is_draw.return_value = False
        is_winner.return_value = False
        self.game.register_player(name='test')

        board = self.game.board.board[:]

        response = self.game.turn(3, 'X')
        board[2] = 'X'

        expected_response = {
            'status': True,
            'board': board,
        }
        self.assertEqual(expected_response, response)

    @mock.patch.object(ComputerPlayer, 'get_move')
    @mock.patch.object(Board, 'put_marker_in_area')
    @mock.patch.object(Board, 'is_free')
    @mock.patch.object(Player, 'is_winner')
    @mock.patch.object(Game, 'is_draw')
    def test_turn_returns_gameover_status(self, is_draw, is_winner, is_free, put_marker_in_area, get_move):
        is_free.return_value = True
        is_draw.return_value = True
        is_winner.return_value = False

        response = self.game.turn(3, 'X')

        expected_response = {
            'status': 'gameover',
            'reason': 'draw',
            'board': self.game.board.board,
        }
        self.assertEqual(expected_response, response)

        is_draw.return_value = False
        is_winner.return_value = True

        response = self.game.turn(3, 'X')

        expected_response = {
            'status': 'gameover',
            'reason': 'win',
            'board': self.game.board.board,
        }
        self.assertEqual(expected_response, response)

    def test_is_draw(self):
        self.assertFalse(self.game.is_draw())
        for x in range(len(self.game.board.board)):
            self.game.board.board[x] = 'X'
        self.assertTrue(self.game.is_draw())


class MyTCPServerHandlerTest(TestCase):
    pass