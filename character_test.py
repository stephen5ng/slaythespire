import logging.config
import unittest

from character import Character

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)


class TestCharacter(unittest.TestCase):
    def test_defend(self):
        character = Character()
        initial_hp = character.hp

        self.assertEqual(5, character.defend(5))
        self.assertEqual(initial_hp - 5, character.hp)

    def test_death_exact(self):
        character = Character(8)
        character.block = 4
        self.assertEqual(8, character.defend(12))
        self.assertEqual(0, character.hp)

    def test_death_overshoot(self):
        character = Character(8)
        character.block = 4

        self.assertEqual(8, character.defend(20))
        self.assertEqual(0, character.hp)

    def test_blocked(self):
        character = Character(8)
        character.block = 10
        initial_hp = character.hp

        self.assertEqual(0, character.defend(7))
        self.assertEqual(8, character.hp)

    def test_vulnerable(self):
        character = Character()
        character.vulnerable(2)

        self.assertEqual(12, character.defend(8))
        character.end_turn()

        self.assertEqual(12, character.defend(8))
        character.end_turn()

        self.assertEqual(8, character.defend(8))
        character.end_turn()

    def test_strength_buff(self):
        character = Character()
        character.strength_buff = 2

        self.assertEqual(0, character.strength)
        character.end_turn()

        self.assertEqual(2, character.strength)
