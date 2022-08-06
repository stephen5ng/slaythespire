import logging
import unittest

import sts
from sts import AttackingPlayer, Card, Deck, Monster


class TestCards(unittest.TestCase):
    def test_card(self):
        self.assertEqual(Card.DEFEND.attack, 0)
        self.assertEqual(Card.STRIKE.attack, 6)

    def test_is_attack(self):
        self.assertFalse(Card.DEFEND.is_attack())


if __name__ == '__main__':
    unittest.main()
