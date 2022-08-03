from re import S
from string import capwords
import unittest
import sts
from sts import Card
from sts import Deck

class TestCards(unittest.TestCase):
    def test_card(self):
        card = Card.DEFEND
        self.assertEqual(card.attack, 0)

        card = Card.STRIKE
        self.assertEqual(card.attack, 6)

class TestPlay(unittest.TestCase):
    def test_play_turn(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        deck = sts.Deck(cards)
        damage = sts.play_turn(deck)
        self.assertEqual(18, damage)

    def test_single_play_game(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        deck = sts.Deck(cards)
        damage = sts.play_game(deck, 1)
        self.assertEqual([18], damage)
    
    def test_multi_play_game(self):
        cards = [Card.DEFEND] + [Card.STRIKE] * 4
        deck = sts.Deck(cards)
        damage = sts.play_game(deck, 2)
        self.assertEqual([18, 36], damage)


class TestDeck(unittest.TestCase):
    def test_empty_deck(self):
        deck = sts.Deck([])
        self.assertEqual(None, deck.deal())

    def test_deal_single_card(self):
        deck = sts.Deck([Card.STRIKE])
        card = deck.deal()

        self.assertEqual(6, card.attack)
        self.assertEqual(None, deck.deal())

        deck.discard([card])
        self.assertEqual(6, deck.deal().attack)

    def test_discard(self):
        deck = sts.Deck([])
        deck.discard([Card.STRIKE])
        self.assertEqual(6, deck.deal().attack)

    def test_multiple_cards(self):
        deck = sts.Deck([Card.DEFEND,
                           Card.STRIKE])

        card0 = deck.deal()
        card1 = deck.deal()
        self.assertEqual(None, deck.deal())

        self.assertEqual(0, card0.attack)
        self.assertEqual(6, card1.attack)

        deck.discard([card0, card1])

        self.assertEqual(0, deck.deal().attack)

    def test_seed(self):
        deck = sts.Deck([Card.DEFEND,
                           Card.STRIKE], seed=2)

        card0 = deck.deal()
        card1 = deck.deal()

        self.assertEqual(6, card0.attack)
        self.assertEqual(0, card1.attack)

    def test_deal_multi(self):
        deck = sts.Deck([Card.DEFEND,
                           Card.STRIKE], seed=2)
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
