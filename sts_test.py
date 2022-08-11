import unittest

import sts
from card import Card
from deck import Deck
from monster import Monster


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


if __name__ == '__main__':
    unittest.main()
