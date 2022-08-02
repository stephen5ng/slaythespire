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
        deck = cards.Deck([cards.Card(attack=8)])

        
if __name__ == '__main__':
    unittest.main()
