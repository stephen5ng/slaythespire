import unittest
import csv_logger
import card

log_history = ""


def fake_logger(fmt, *args):
    global log_history
    print(f"logging: {fmt % args}")
    log_history += fmt % args + "\n"


class TestCsvLogger(unittest.TestCase):
    def setUp(self) -> None:
        self.logger = csv_logger.CsvLogger(fake_logger)
        return super().setUp()

    def tearDown(self) -> None:
        global log_history
        log_history = ""
        return super().tearDown()

    def test_simple_log(self):
        global log_history
        self.logger.play_card(3, card.Card.ANGER, 10, 9, 8, 7)
        self.logger.next_turn()
        self.logger.end_game(5)
        expected = """FINAL_HP,GAME,N_TURN,N_PLAY,ENERGY,PLAY,ATTACK,VULNERABLE,DEFEND,PLAYER_HP,MONSTER_HP,MONSTER_ATTACK,MONSTER_BLOCK
5,0,0,0,3,ANGER,0,0,0,10,9,8,7
"""
        self.assertEqual(expected, log_history)

    def test_complex_log(self):
        global log_history
        self.logger.play_card(3, card.Card.ANGER, 10, 9, 8, 7)
        self.logger.play_card(3, card.Card.BASH, 10, 9, 8, 7)
        self.logger.next_turn()
        self.logger.play_card(3, card.Card.DEFEND, 10, 9, 8, 7)
        self.logger.next_turn()
        self.logger.end_game(20)
        self.logger.play_card(3, card.Card.DEMON_FORM, 10, 9, 8, 7)
        self.logger.next_turn()
        self.logger.end_game(10)

        expected = """FINAL_HP,GAME,N_TURN,N_PLAY,ENERGY,PLAY,ATTACK,VULNERABLE,DEFEND,PLAYER_HP,MONSTER_HP,MONSTER_ATTACK,MONSTER_BLOCK
20,0,0,0,3,ANGER,0,0,0,10,9,8,7
20,0,0,1,3,BASH,8,2,0,10,9,8,7
20,0,1,0,3,DEFEND,0,0,5,10,9,8,7
10,1,0,0,3,DEMON_FORM,0,0,0,10,9,8,7
"""
        # expected = '\n'.join(
        #     ["0,0,0,ANGER", "0,0,1,BASH", "0,1,0,DEFEND", "1,0,0,DEMON_FORM"]) + "\n"

        self.assertEqual(expected, log_history)


if __name__ == '__main__':
    unittest.main()
