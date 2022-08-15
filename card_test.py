import logging.config
import unittest

from card import Card

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)

class TestCards(unittest.TestCase):
    def test_card(self):
        self.assertEqual(Card.DEFEND.attack, 0)
        self.assertEqual(Card.STRIKE.attack, 6)

    def test_is_attack(self):
        self.assertFalse(Card.DEFEND.is_attack())


if __name__ == '__main__':
    unittest.main()
