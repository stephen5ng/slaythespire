import logging.config
import unittest

import sts
from card import Card
from deck import Deck
from monster import JawWorm, JawWormMode, Monster

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)

class TestMonster(unittest.TestCase):
    def test_defend(self):
        monster = Monster()
        initial_hp = monster.hp
        monster.begin_turn()
        monster.defend(5)

        self.assertEqual([5], monster.get_damage())
        self.assertEqual(initial_hp - 5, monster.hp)

    def test_death_exact(self):
        monster = Monster(8)
        monster.block = 4
        monster.begin_turn()
        monster.defend(12)

        self.assertEqual(0, monster.hp)
        self.assertEqual([8], monster.get_damage())

    def test_death_overshoot(self):
        monster = Monster(8)
        monster.block = 4
        monster.begin_turn()
        monster.defend(20)

        self.assertEqual(0, monster.hp)
        self.assertEqual([8], monster.get_damage())

    def test_blocked(self):
        monster = Monster(8)
        monster.block = 10
        initial_hp = monster.hp
        monster.begin_turn()
        monster.defend(7)

        self.assertEqual(8, monster.hp)
        self.assertEqual([0], monster.get_damage())

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


class JawWormForTesting(JawWorm):
    def __init__(self) -> None:
        super().__init__()
        self.next_mode = JawWormMode.CHOMP

    def _get_next_mode(self):
        return self.next_mode


class TestJawWorm(unittest.TestCase):
    def test_initial(self):
        jw = JawWorm()
        self.assertEqual(12, jw.attack())
        self.assertEqual(0, jw.strength)
        self.assertEqual(0, jw.block)

    def test_initial_defend(self):
        jw = JawWorm()
        jw.defend(8)
        self.assertEqual(32, jw.hp)

    def test_bellow(self):
        jw = JawWormForTesting()
        jw.next_mode = JawWormMode.BELLOW
        jw.end_turn()
        self.assertEqual(0, jw.attack())
        self.assertEqual(6, jw.block)
        self.assertEqual(4, jw.strength)

    def test_strength(self):
        jw = JawWormForTesting()
        jw.next_mode = JawWormMode.BELLOW
        jw.end_turn()
        self.assertEqual(4, jw.strength)

        jw.next_mode = JawWormMode.CHOMP
        jw.end_turn()
        self.assertEqual(3, jw.strength)
        jw.end_turn()
        self.assertEqual(2, jw.strength)
        jw.end_turn()
        self.assertEqual(1, jw.strength)
        jw.end_turn()
        self.assertEqual(0, jw.strength)
        jw.end_turn()
        self.assertEqual(0, jw.strength)
        jw.end_turn()

        jw.next_mode = JawWormMode.BELLOW
        jw.end_turn()
        self.assertEqual(4, jw.strength)
        jw.end_turn()
        self.assertEqual(7, jw.strength)

    def test_thrash(self):
        jw = JawWormForTesting()
        jw.next_mode = JawWormMode.THRASH
        jw.end_turn()
        self.assertEqual(5, jw.block)

    def test_block(self):
        jw = JawWormForTesting()

        jw.next_mode = JawWormMode.THRASH
        self.assertEqual(40, jw.hp)
        jw.end_turn()
        self.assertEqual(5, jw.block)
        jw.defend(3)
        self.assertEqual(2, jw.block)
        self.assertEqual(40, jw.hp)
        jw.defend(10)
        self.assertEqual(0, jw.block)
        self.assertEqual(32, jw.hp)

        jw.next_mode = JawWormMode.CHOMP
        jw.end_turn()
        self.assertEqual(0, jw.block)

    def test_generate_mode(self):
        jw = JawWorm()
        for i in range(50):
            jw.end_turn()
        modes = ''.join([m.name for m in jw._modes])
        print(f"MODES: {modes}")
        self.assertNotIn('BELLOWBELLOW', modes)
        self.assertNotIn('THRASHTHRASHTHRASH', modes)
        self.assertIn('THRASHTHRASH', modes)
        self.assertNotIn('CHOMPCHOMP', modes)

if __name__ == '__main__':
    unittest.main()
