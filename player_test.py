import logging
import logging.config
import unittest

from card import Card
from deck import Deck
from monster import Monster
from player import AttackingPlayer

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
turn_logger = logging.getLogger("turns")
logger = logging.getLogger("sts")


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.monster = Monster()

    def test_play_turn(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        deck = Deck(cards)
        AttackingPlayer(deck).play_turn(self.monster)

        self.assertEqual([18], self.monster.get_damage())
        self.assertEqual(5, len(cards), msg='input cards was mutated')

    def test_play_turn_no_energy(self):
        cards = [Card.ANGER] + [Card.STRIKE] * 4
        deck = Deck(cards)
        AttackingPlayer(deck).play_turn(self.monster)

        self.assertEqual([24], self.monster.get_damage())
        self.assertEqual([
            Card.ANGER, Card.ANGER, Card.STRIKE, Card.STRIKE, Card.STRIKE, Card.STRIKE
        ], deck.discards)

    def test_play_turn_until_monster_dead(self):
        monster = Monster(10)

        cards = [Card.STRIKE] * 5
        deck = Deck(cards)
        AttackingPlayer(deck).play_turn(monster)

        self.assertEqual([12], monster.get_damage())

    def test_play_turn_strike_bonus(self):
        cards = [Card.PERFECTED_STRIKE] + [Card.STRIKE] * 4
        deck = Deck(cards)
        AttackingPlayer(deck).play_turn(self.monster)

        self.assertEqual([22], self.monster.get_damage())

    def test_play_turn_draw_card(self):
        cards = [Card.POMMEL_STRIKE] + [Card.STRIKE] * 4 + [Card.BASH]
        deck = Deck(cards)
        AttackingPlayer(deck).play_turn(self.monster)

        self.assertEqual([16], self.monster.get_damage())

    def test_play_turn_vulnerable(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 3 + [Card.BASH]
        AttackingPlayer(Deck(cards)).play_turn(self.monster)

        self.assertEqual([17], self.monster.get_damage())

    def test_play_turn_strength_buff(self):
        cards = [Card.DEMON_FORM] + [Card.STRIKE] * 4
        player = AttackingPlayer(Deck(cards))
        player.play_turn(self.monster)
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([0, 8*3, 10*3], self.monster.get_damage())

    def test_play_turn_strength_gain(self):
        cards = [Card.INFLAME] + [Card.STRIKE] * 4
        player = AttackingPlayer(Deck(cards))
        player.play_turn(self.monster)
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([8*2, 8*3, 8*3], self.monster.get_damage())

    def test_play_turn_strength_multiplier(self):
        cards = [Card.INFLAME] + [Card.STRIKE] * 3 + [Card.LIMIT_BREAK_PLUS]
        player = AttackingPlayer(Deck(cards))
        player.play_turn(self.monster)
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([6+4, 2*(6+8), 2*(6+16)], self.monster.get_damage())

    def test_play_turn_flex(self):
        cards = [Card.FLEX] + [Card.STRIKE] * 9
        player = AttackingPlayer(Deck(cards, shuffle=False))
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([8*3, 6*3], self.monster.get_damage())

    def test_play_turn_attack_multiplier(self):
        cards = [Card.TWIN_STRIKE] + [Card.DEFEND] * 4
        player = AttackingPlayer(Deck(cards))
        player.play_turn(self.monster)

        self.assertEqual([10], self.monster.get_damage())

    def test_play_turn_exhaustible(self):
        cards = [Card.DEMON_FORM] + [Card.BASH] + [Card.DEFEND] * 3
        deck = Deck(cards)
        AttackingPlayer(deck, energy=5).play_turn(self.monster)

        self.assertNotIn(Card.DEMON_FORM, deck.discards)
        # Exhausting DEMON_FORM should not affect BASH
        self.assertEqual([8], self.monster.get_damage())

    def test_single_play_game(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        AttackingPlayer(Deck(cards)).play_game(self.monster, 1)

        self.assertEqual([18], self.monster.get_damage())

    def test_multi_play_game(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        AttackingPlayer(Deck(cards)).play_game(self.monster, 2)

        self.assertEqual([18, 18], self.monster.get_damage())

    def test_play_game_monster_dies(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        monster = Monster()
        deck = Deck(cards)
        monster.hp = 16
        AttackingPlayer(deck).play_game(monster, 2)

        self.assertEqual([16], monster.get_damage())
        self.assertEqual(1, deck._deals)


if __name__ == '__main__':
    unittest.main()
