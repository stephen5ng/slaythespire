import logging
from typing import Union

from card import Card

logger = logging.getLogger("turns").getChild(__name__)


class Character:

    def __init__(self, hp: int = 70) -> None:
        self._vulnerable = 0
        self._weak = 0
        self._turn = 0
        self.block = 0
        self.hp = hp
        self.strength = 0
        self.strength_buff = 0

    def defend(self, attack_damage: int) -> int:
        logger.info(
            f"{self.__class__.__name__} defend({attack_damage}) block: {self.block}, vulnerable: {self._vulnerable}, hp: {self.hp}")

        post_vulnerable_damage = int(
            attack_damage * (1.5 if self._vulnerable else 1.0))

        post_block_damage = max(0, post_vulnerable_damage - self.block)
        self.block = max(0, self.block - post_vulnerable_damage)

        post_hp_damage = min(self.hp, post_block_damage)
        self.hp -= post_hp_damage

        logger.info(
            f"{self.__class__.__name__} ...defend() block: {self.block},"
            f" damage: {attack_damage}->{post_vulnerable_damage}->{post_block_damage}->{post_hp_damage}, hp: {self.hp}")
        if not self.hp:
            logger.info(f"{self.__class__.__name__} DIED")
        return post_hp_damage

    def vulnerable(self, turns: int) -> None:
        self._vulnerable += turns
        logger.debug(f"{self.__class__.__name__} vulnerable({turns}), vulnerable: {self._vulnerable}")

    def end_turn(self):
        if self._vulnerable > 0:
            self._vulnerable -= 1
        self.strength += self.strength_buff
        if self._weak > 0:
            self._weak -= 1
        self._turn += 1
        logger.debug(f"{self.__class__.__name__} end_turn vulnerable({self._vulnerable}), self.strength: {self.strength}")

    def get_turn(self):
        return self._turn

    turn = property(get_turn)
