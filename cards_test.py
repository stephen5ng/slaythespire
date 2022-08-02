import unittest
import cards


class TestCards(unittest.TestCase):
    def test_card(self):
        card = cards.Card(attack=8)
        self.assertEqual(card.attack, 8)

        card = cards.Card(attack=2)
        self.assertEqual(card.attack, 2)


class TestDeck(unittest.TestCase):
    def test_empty_deck(self):
        deck = cards.Deck([])
        self.assertEqual(None, deck.deal())

    def test_deal_single_card(self):
        deck = cards.Deck([cards.Card(attack=8)])
        card = deck.deal()

        self.assertEqual(8, card.attack)
        self.assertEqual(None, deck.deal())

        deck.discard([card])
        self.assertEqual(8, deck.deal().attack)

    def test_discard(self):
        deck = cards.Deck([])
        deck.discard([cards.Card(attack=8)])
        self.assertEqual(8, deck.deal().attack)

    def test_multiple_cards(self):
        deck = cards.Deck([cards.Card(attack=8),
                           cards.Card(attack=6)])

        card0 = deck.deal()
        card1 = deck.deal()
        self.assertEqual(None, deck.deal())

        self.assertEqual(8, card0.attack)
        self.assertEqual(6, card1.attack)

        deck.discard([card0, card1])

        self.assertEqual(8, deck.deal().attack)

    def test_seed(self):
        deck = cards.Deck([cards.Card(attack=8),
                           cards.Card(attack=6)], seed=2)

        card0 = deck.deal()
        card1 = deck.deal()

        self.assertEqual(6, card0.attack)
        self.assertEqual(8, card1.attack)

    def test_deal_multi(self):
        deck = cards.Deck([cards.Card(attack=8),
                           cards.Card(attack=6)], seed=2)
        c = deck.deal_multi(1)
        self.assertEqual(1, len(c))
        self.assertEqual(6, c[0].attack)

        c = deck.deal_multi(2)
        self.assertEqual(1, len(c))
        self.assertEqual(8, c[0].attack)

        c = deck.deal_multi(1)
        self.assertEqual(0, len(c))

if __name__ == '__main__':
    unittest.main()
