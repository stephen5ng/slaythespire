import unittest
import logging
from string import capwords

import sts
from sts import Card, Deck, Monster, Player


class TestDamage(unittest.TestCase):
    def test_scaling_damage(self):
        self.assertEqual("O(1)",
                         sts.format_scaling_damage([17, -0.0, -0.0, 0]))

        self.assertEqual("O(7*n)",
                         sts.format_scaling_damage([17, 6.9, 0.2, 0]))

        self.assertEqual("O(7*n + 1*n^2)",
                         sts.format_scaling_damage([17, 6.9, 1.3, 0]))

        self.assertEqual("O(7*n + 1*n^2 + 4*n^3)",
                         sts.format_scaling_damage([17, 6.9, 1.3, 4.0]))


class TestCards(unittest.TestCase):
    def test_card(self):
        self.assertEqual(Card.DEFEND.attack, 0)
        self.assertEqual(Card.STRIKE.attack, 6)


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.monster = Monster()

    def test_play_turn(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        deck = Deck(cards)
        Player(deck).play_turn(self.monster)

        self.assertEqual([18], self.monster.get_damage())
        self.assertEqual(5, len(cards), msg='input cards was mutated')

    def test_play_turn_no_energy(self):
        cards = [Card.ANGER] + [Card.STRIKE] * 4
        deck = Deck(cards)
        Player(deck).play_turn(self.monster)

        self.assertEqual([24], self.monster.get_damage())
        self.assertEqual([
            Card.ANGER, Card.ANGER, Card.STRIKE, Card.STRIKE, Card.STRIKE, Card.STRIKE
        ], deck.discards)

    def test_play_turn_vulnerable(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 3 + [Card.BASH]
        Player(Deck(cards)).play_turn(self.monster)

        self.assertEqual([17], self.monster.get_damage())

    def test_play_turn_strength_buff(self):
        cards = [Card.DEMON_FORM] + [Card.STRIKE] * 4
        player = Player(Deck(cards))
        player.play_turn(self.monster)
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([0, 8*3, 10*3], self.monster.get_damage())

    def test_play_turn_strength_gain(self):
        cards = [Card.INFLAME] + [Card.STRIKE] * 4
        player = Player(Deck(cards))
        player.play_turn(self.monster)
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([8*2, 8*3, 8*3], self.monster.get_damage())

    def test_play_turn_flex(self):
        cards = [Card.FLEX] + [Card.STRIKE] * 9
        player = Player(Deck(cards, shuffle=False))
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([8*3, 6*3], self.monster.get_damage())

    def test_play_turn_attack_multiplier(self):
        cards = [Card.TWIN_STRIKE] + [Card.DEFEND] * 4
        player = Player(Deck(cards))
        player.play_turn(self.monster)

        self.assertEqual([10], self.monster.get_damage())

    def test_play_turn_exhaustible(self):
        cards = [Card.DEMON_FORM] + [Card.STRIKE] * 3 + [Card.BASH]
        deck = Deck(cards)
        Player(deck).play_turn(self.monster)

        self.assertNotIn(Card.DEMON_FORM, deck.discards)

    def test_single_play_game(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        Player(Deck(cards)).play_game(self.monster, 1)

        self.assertEqual([18], self.monster.get_damage())

    def test_multi_play_game(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        Player(Deck(cards)).play_game(self.monster, 2)

        self.assertEqual([18, 18], self.monster.get_damage())


class TestMonster(unittest.TestCase):
    def test_defend(self):
        monster = Monster()
        monster.begin_turn()
        monster.defend(5)

        self.assertEqual([5], monster.get_damage())

    def test_vulnerable(self):
        monster = Monster()

        monster.begin_turn()
        monster.vulnerable(2)
        monster.defend(8)
        monster.end_turn()

        monster.begin_turn()
        monster.defend(8)
        monster.end_turn()

        monster.begin_turn()
        monster.defend(8)
        monster.end_turn()

        self.assertEqual([12, 12, 8], monster.get_damage())


class TestDeck(unittest.TestCase):
    def test_empty_deck(self):
        deck = Deck([])
        self.assertEqual(None, deck.deal())

    def test_deal_single_card(self):
        deck = Deck([Card.STRIKE])
        card = deck.deal()

        self.assertEqual(6, card.attack)
        self.assertEqual(None, deck.deal())

        deck.discard([card])
        self.assertEqual(6, deck.deal().attack)

    def test_discard(self):
        deck = Deck([])
        deck.discard([Card.STRIKE])
        self.assertEqual(6, deck.deal().attack)

    def test_multiple_cards(self):
        deck = Deck([Card.DEFEND, Card.STRIKE])

        card0 = deck.deal()
        card1 = deck.deal()
        self.assertEqual(None, deck.deal())

        self.assertEqual(0, card0.attack)
        self.assertEqual(6, card1.attack)

        deck.discard([card0, card1])

        self.assertEqual(0, deck.deal().attack)

    def test_seed(self):
        deck = Deck([Card.DEFEND, Card.STRIKE], seed=2)

        card0 = deck.deal()
        card1 = deck.deal()

        self.assertEqual(6, card0.attack)
        self.assertEqual(0, card1.attack)

    def test_deal_multi(self):
        deck = Deck([Card.DEFEND, Card.STRIKE], seed=2)
        cards = deck.deal_multi(1)
        self.assertEqual(1, len(cards))
        self.assertEqual(6, cards[0].attack)

        cards = deck.deal_multi(2)
        self.assertEqual(1, len(cards))
        self.assertEqual(0, cards[0].attack)

        cards = deck.deal_multi(1)
        self.assertEqual(0, len(cards))


if __name__ == '__main__':
    unittest.main()
