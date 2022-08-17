import logging
import sys
from enum import Enum, auto
from typing import Sequence

import numpy

from character import Character

logger = logging.getLogger("turns").getChild(__name__)


class Monster(Character):
    def __init__(self, hp=sys.maxsize) -> None:
        super().__init__(hp=hp)
        self._damage = []

    def begin_turn(self):
        pass

    def attack(self):
        pass

    def defend(self, attack_damage: int) -> None:
        post_hp_damage = super().defend(attack_damage)

        array_gap = 1 + self._turn - len(self._damage)
        if array_gap:
            self._damage.extend([0]*array_gap)

        self._damage[self._turn] += post_hp_damage
        if not self.hp:
            logger.info("MONSTER DIED")

    def get_damage(self) -> Sequence:
        return self._damage

    def end_turn(self):
        super().end_turn()
        logger.info(f"damage: {self._damage}")


class JawWormMode(Enum):
    CHOMP = auto()
    THRASH = auto()
    BELLOW = auto()


class JawWorm(Monster):
    def __init__(self) -> None:
        super().__init__(hp=40)
        self.strength = 0
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
        logger.debug(f"JawWorm attack() --> {damage}")
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
