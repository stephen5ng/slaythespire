from string import capwords
import unittest
import sts


class TestCards(unittest.TestCase):
    def test_card(self):
        card = sts.Card(attack_damage=8)
        self.assertEqual(card.attack_damage, 8)

        card = sts.Card(attack_damage=2)
        self.assertEqual(card.attack_damage, 2)

class TestMonster(unittest.TestCase):
    pass
class TestDeck(unittest.TestCase):
    def test_empty_deck(self):
        deck = sts.Deck([])
        self.assertEqual(None, deck.deal())

    def test_deal_single_card(self):
        deck = sts.Deck([sts.Card(attack_damage=8)])
        card = deck.deal()

        self.assertEqual(8, card.attack_damage)
        self.assertEqual(None, deck.deal())

        deck.discard([card])
        self.assertEqual(8, deck.deal().attack_damage)

    def test_discard(self):
        deck = sts.Deck([])
        deck.discard([sts.Card(attack_damage=8)])
        self.assertEqual(8, deck.deal().attack_damage)

    def test_multiple_cards(self):
        deck = sts.Deck([sts.Card(attack_damage=8),
                           sts.Card(attack_damage=6)])

        card0 = deck.deal()
        card1 = deck.deal()
        self.assertEqual(None, deck.deal())

        self.assertEqual(8, card0.attack_damage)
        self.assertEqual(6, card1.attack_damage)

        deck.discard([card0, card1])

        self.assertEqual(8, deck.deal().attack_damage)

    def test_seed(self):
        deck = sts.Deck([sts.Card(attack_damage=8),
                           sts.Card(attack_damage=6)], seed=2)

        card0 = deck.deal()
        card1 = deck.deal()

        self.assertEqual(6, card0.attack_damage)
        self.assertEqual(8, card1.attack_damage)

    def test_deal_multi(self):
        deck = sts.Deck([sts.Card(attack_damage=8),
                           sts.Card(attack_damage=6)], seed=2)
        cards = deck.deal_multi(1)
        self.assertEqual(1, len(cards))
        self.assertEqual(6, cards[0].attack_damage)

        cards = deck.deal_multi(2)
        self.assertEqual(1, len(cards))
        self.assertEqual(8, cards[0].attack_damage)

        cards = deck.deal_multi(1)
        self.assertEqual(0, len(cards))

if __name__ == '__main__':
    unittest.main()
