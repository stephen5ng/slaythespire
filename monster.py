import logging
from enum import Enum, auto

import numpy

logging.basicConfig(filename='sts.log', encoding='utf-8', level=logging.INFO)


class Monster:
    def __init__(self) -> None:
        self._damage = []
        self._turn = 0
        self._vulnerable = 0

    def begin_turn(self):
        pass

    def defend(self, attack: int):
        array_gap = 1 + self._turn - len(self._damage)
        if array_gap:
            self._damage.extend([0]*array_gap)

        self._damage[self._turn] += int(attack *
                                        (1.5 if self._vulnerable else 1.0))
        logging.debug(
            f"{self._turn}: MONSTER TAKING DAMAGE: vuln: {self._vulnerable}: {attack} -> {self._damage[self._turn]}")

    def vulnerable(self, turns: int):
        self._vulnerable += turns
        logging.debug(
            f"{self._turn}: MONSTER TAKING VULNERABLE:{turns} -> {self._vulnerable}")

    def end_turn(self):
        if self._vulnerable > 0:
            self._vulnerable -= 1
        self._turn += 1


    def get_damage(self):
        return self._damage


class JawWormMode(Enum):
    CHOMP = auto()
    THRASH = auto()
    BELLOW = auto()


class JawWorm(Monster):
    def __init__(self) -> None:
        super().__init__()
        self.block = 0
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

    def defend(self, damage: int):
        super().defend(damage)
        if damage <= self.block:
            self.block -= damage
            return
        
        damage -= self.block
        self.block = 0
        self.hp -= damage

    def attack(self):
        if self._mode == JawWormMode.CHOMP:
            return 12 + self.strength
        if self._mode == JawWormMode.BELLOW:
            return 7 + self.strength

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
