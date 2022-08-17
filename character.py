import logging
from typing import Union

from card import Card

logger = logging.getLogger("turns").getChild(__name__)


class Character:

    def __init__(self, hp: int = 70) -> None:
        self._vulnerable = 0
        self._damage = []
        self._turn = 0
        self.block = 0
        self.hp = hp

    def defend(self, attack_damage: int) -> int:
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
            logger.info("CHARACTER DIED")
        return post_hp_damage

    def vulnerable(self, turns: int) -> None:
        self._vulnerable += turns
        logger.debug(f"vulnerable({turns}), vulnerable: {self._vulnerable}")

    def end_turn(self):
        if self._vulnerable > 0:
            self._vulnerable -= 1
        self._turn += 1
        logger.info(f"damage: {self._damage}")
