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
        self.planned_damage = 0

    def attack(self) -> int:
        return int(self.planned_damage + self.strength)

    def defend(self, attack_damage: int) -> None:
        post_hp_damage = super().defend(attack_damage)

        array_gap = 1 + self._turn - len(self._damage)
        if array_gap:
            self._damage.extend([0]*array_gap)

        self._damage[self._turn] += post_hp_damage

    def get_damage(self) -> Sequence:
        return self._damage

    def end_turn(self):
        super().end_turn()
        self._damage
        logger.info(f"damage: {self._damage}")


class JawWormMode(Enum):
    CHOMP = auto() #srot command line
    THRASH = auto()
    BELLOW = auto()

# average player hp
class JawWorm(Monster):
    def __init__(self) -> None:
        super().__init__(hp=40)
        self.strength = 0
        self._mode = JawWormMode.CHOMP
        self._modes = [self._mode]
        self._setup_mode()

    def _get_next_mode(self):
        while True:
            r = numpy.random.randint(100)
            if r <= 45:
                next_mode = JawWormMode.BELLOW
                if self._modes[-1] == JawWormMode.BELLOW:
                    continue
            elif r <= 75:
                next_mode = JawWormMode.THRASH
                if self._modes[-1] == JawWormMode.THRASH and self._modes[-2] == JawWormMode.THRASH: # check the length
                    continue
            else:
                if self._modes[-1] == JawWormMode.CHOMP:
                    continue
                next_mode = JawWormMode.CHOMP
            break
        self._modes.append(next_mode)
        logger.debug(f"JawWorm next_mode: {self._mode.name}")
        return next_mode

    def attack(self) -> int:
        # logger.debug(f"JawWorm attack() {self._mode.name}--> {self.planned_damage}")
        return self.planned_damage + self.strength if self.planned_damage else 0

    def _setup_mode(self):
        self.planned_damage = 0
        if self._mode == JawWormMode.CHOMP:
            self.planned_damage = 12
        elif self._mode == JawWormMode.THRASH:
            self.block = 5
            self.planned_damage = 7
        elif self._mode == JawWormMode.BELLOW:
            self.strength += 4
            self.block = 6
            
    def end_turn(self):
        super().end_turn()
        self.block = 0

        self._mode = self._get_next_mode()
        self._setup_mode()
        logger.debug(f"end_turn(): {self}")

    def __str__(self):
        return f"JawWorm {self._mode}, hp: {self.hp}, planned_damage: {self.planned_damage}, block: {self.block}, strength: {self.strength}, vulnerable: {self._vulnerable}"

class Cultist(Monster):
    def __init__(self) -> None:
        super().__init__(hp=80)
        self.strength_buff = 4
    
    def end_turn(self):
        self.planned_damage = 6
