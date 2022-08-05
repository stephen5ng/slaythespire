import logging
import unittest
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

    def test_play_turn_strike_bonus(self):
        cards = [Card.PERFECTED_STRIKE] + [Card.STRIKE] * 4
        deck = Deck(cards)
        Player(deck).play_turn(self.monster)

        self.assertEqual([22], self.monster.get_damage())

    def test_play_turn_draw_card(self):
        cards = [Card.POMMEL_STRIKE] + [Card.STRIKE] * 4 + [Card.BASH]
        deck = Deck(cards)
        Player(deck).play_turn(self.monster)

        self.assertEqual([16], self.monster.get_damage())

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

    def test_play_turn_strength_multiplier(self):
        cards = [Card.INFLAME] + [Card.STRIKE] * 3 + [Card.LIMIT_BREAK_PLUS]
        player = Player(Deck(cards))
        player.play_turn(self.monster)
        player.play_turn(self.monster)
        player.play_turn(self.monster)

        self.assertEqual([6+4, 2*(6+8), 2*(6+16)], self.monster.get_damage())

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
        cards = [Card.DEMON_FORM] + [Card.BASH] + [Card.DEFEND] * 3
        deck = Deck(cards)
        Player(deck, energy=5).play_turn(self.monster)

        self.assertNotIn(Card.DEMON_FORM, deck.discards)
        # Exhausting DEMON_FORM should not affect BASH
        self.assertEqual([8], self.monster.get_damage())

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
        self.assertEqual([], deck.deal())

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
