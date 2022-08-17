import logging
import sys
from enum import Enum, auto
from typing import Sequence

import numpy

logger = logging.getLogger("turns").getChild(__name__)


class Monster:
    def __init__(self, hp=sys.maxsize) -> None:
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
        logger.info(
            f"defend({attack_damage}) block: {self.block}, vulnerable: {self._vulnerable}, hp: {self.hp}")

        array_gap = 1 + self._turn - len(self._damage)
        if array_gap:
            self._damage.extend([0]*array_gap)

        post_vulnerable_damage = int(
            attack_damage * (1.5 if self._vulnerable else 1.0))

        post_block_damage = max(0, post_vulnerable_damage - self.block)
        self.block = max(0, self.block - post_vulnerable_damage)

        post_hp_damage = min(self.hp, post_block_damage)
        self.hp -= post_hp_damage

        self._damage[self._turn] += post_hp_damage
        logger.info(
            f"...defend() block: {self.block},"
            f" damage: {attack_damage}->{post_vulnerable_damage}->{post_block_damage}->{post_hp_damage}, hp: {self.hp}")
        if not self.hp:
            logger.info("MONSTER DIED")

    def vulnerable(self, turns: int) -> None:
        self._vulnerable += turns
        logger.debug(f"vulnerable({turns}), vulnerable: {self._vulnerable}")

    def end_turn(self):
        if self._vulnerable > 0:
            self._vulnerable -= 1
        self._turn += 1
        logger.info(f"damage: {self.get_damage()}")

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
