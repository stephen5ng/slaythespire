import logging
import unittest
from string import capwords

import sts
from sts import Card, Deck, Monster, AttackingPlayer


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
        self.assertEqual([], deck.deal())

    def test_discard(self):
        deck = Deck([Card.STRIKE]*4 + [Card.DEFEND])
        cards = deck.deal(5)
        deck.discard(deck.hand)
        self.assertEqual(0, len(deck.hand))
        self.assertEqual(5, len(deck.discards))

    def test_exhaust(self):
        deck = Deck([Card.STRIKE]*4 + [Card.DEFEND])
        cards = deck.deal(5)
        deck.exhaust(deck.hand)
        self.assertEqual(0, len(deck.hand))
        self.assertEqual(5, len(deck.exhausted))

    def test_deal_single_card(self):
        deck = Deck([Card.STRIKE])
        card = deck.deal()[0]

        self.assertEqual(6, card.attack)
        self.assertEqual([], deck.deal())

        deck.discard([card])
        self.assertEqual(6, deck.deal()[0].attack)

    def test_card_movement(self):
        deck = Deck([Card.STRIKE])
        self.assertEqual(1, len(deck.deck))
        self.assertEqual(0, len(deck.hand))
        self.assertEqual(0, len(deck.discards))

        cards = deck.deal()
        self.assertEqual(0, len(deck.deck))
        self.assertEqual(1, len(deck.hand))
        self.assertEqual(0, len(deck.discards))

        deck.discard(cards)
        self.assertEqual(0, len(deck.deck))
        self.assertEqual(0, len(deck.hand))
        self.assertEqual(1, len(deck.discards))

    def test_multiple_cards(self):
        deck = Deck([Card.DEFEND, Card.STRIKE])

        card0, card1 = deck.deal(2)
        self.assertEqual([], deck.deal())

        self.assertEqual(0, card0.attack)
        self.assertEqual(6, card1.attack)

        deck.discard([card0, card1])

        self.assertEqual(0, deck.deal()[0].attack)

    def test_seed(self):
        deck = Deck([Card.DEFEND, Card.STRIKE], seed=2)

        card0, card1 = deck.deal(2)

        self.assertEqual(6, card0.attack)
        self.assertEqual(0, card1.attack)

    def test_deal_multi(self):
        deck = Deck([Card.DEFEND, Card.STRIKE], seed=2)
        cards = deck.deal(1)
        self.assertEqual(1, len(cards))
        self.assertEqual(6, cards[0].attack)

        cards = deck.deal(2)
        self.assertEqual(1, len(cards))
        self.assertEqual(0, cards[0].attack)

        cards = deck.deal(1)
        self.assertEqual(0, len(cards))


if __name__ == '__main__':
    unittest.main()
