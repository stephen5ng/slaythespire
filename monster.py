import logging

from enum import Enum, auto
from typing import Sequence

import numpy

logger = logging.getLogger("turns").getChild(__name__)

class Monster:
    def __init__(self, hp=1000) -> None:
        self._damage = []
        self._turn = 0
        self._vulnerable = 0
        self.block = 0
        self.hp = hp

    def begin_turn(self):
        pass

    def attack(self):
        pass

    def defend(self, attack_damage: int) -> None:
        array_gap = 1 + self._turn - len(self._damage)
        if array_gap:
            self._damage.extend([0]*array_gap)

        damage = int(attack_damage * (1.5 if self._vulnerable else 1.0))

        if damage <= self.block:
            self.block -= damage
            return

        post_block_damage = damage - self.block
        self.block = 0

        self.hp = max(0, self.hp - post_block_damage)
        self._damage[self._turn] += post_block_damage
        logger.debug(
            f"{self._turn}: defend() block: {self.block}, vuln: {self._vulnerable}, damage: {attack_damage}->{damage}->{post_block_damage}, hp: {self.hp}")

    def vulnerable(self, turns: int) -> None:
        self._vulnerable += turns
        logger.debug(
            f"{self._turn}: vulnerable({turns}), vuln: {self._vulnerable}")

    def end_turn(self):
        if self._vulnerable > 0:
            self._vulnerable -= 1
        self._turn += 1

    def get_damage(self) -> Sequence:
        return self._damage


class JawWormMode(Enum):
    CHOMP = auto()
    THRASH = auto()
    BELLOW = auto()


class JawWorm(Monster):
    def __init__(self) -> None:
        super().__init__()
        self.strength = 0
        self.hp = 40
        self._mode = JawWormMode.CHOMP

    def _get_next_mode(self):
        r = numpy.random.randint(100)
        if r <= 45:
            return JawWormMode.BELLOW
        elif r <= 75:
            return JawWormMode.THRASH
        return JawWormMode.CHOMP

    def attack(self):
        damage = None
        if self._mode == JawWormMode.CHOMP:
            damage = 12 + self.strength
        if self._mode == JawWormMode.BELLOW:
            damage = 7 + self.strength
        logger.debug(f"JawWorm attack() damage: {damage}")
        return damage

    def end_turn(self):
        super().end_turn()
        self.block = 0
        self.strength = max(0, self.strength-1)

        self._mode = self._get_next_mode()

        if self._mode == JawWormMode.THRASH:
            self.block = 5
        elif self._mode == JawWormMode.BELLOW:
            self.block = 6
            self.strength += 4
        logger.debug(f"end_turn(): {self}")

    def __str__(self):
        return f"JawWorm {self._mode}, hp: {self.hp}, block: {self.block}, strength: {self.strength}, vulnerable: {self._vulnerable}"
