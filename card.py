
from collections import namedtuple
from enum import Enum
import logging

logger = logging.getLogger("turns").getChild(__name__)


class CardArgs(namedtuple('CardArgs', (
    'energy '
    'attack '
    'attack_multiplier '
    'attack_strength_multiplier '
    'block '
    'draw_card '
    'enemy_strength_gain '
    'exhausts '
    'strength_buff '
    'strength_gain '
    'strength_loss '
    'strength_multiplier '
    'strike_bonus '
    'vulnerable '
        'weaken'))):
    def __new__(cls, energy,
                attack=0,
                attack_multiplier=1,
                attack_strength_multiplier=1,
                block=0,
                draw_card=0,
                enemy_strength_gain=0,
                exhausts=False,
                strength_buff=0,
                strength_gain=0,
                strength_loss=0,
                strength_multiplier=1,
                strike_bonus=0,
                vulnerable=0,
                weaken=0):
        return super().__new__(cls, energy,
                               attack,
                               attack_multiplier,
                               attack_strength_multiplier,
                               block,
                               draw_card,
                               enemy_strength_gain,
                               exhausts,
                               strength_buff,
                               strength_gain,
                               strength_loss,
                               strength_multiplier,
                               strike_bonus,
                               vulnerable,
                               weaken)

    def __getnewargs__(self):
        return (self.energy,
                self.attack,
                self.attack_multiplier,
                self.attack_strength_multiplier,
                self.block,
                self.draw_card,
                self.exhausts,
                self.strength_gain,
                self.strength_buff,
                self.strength_multiplier,
                self.strike_bonus,
                self.vulnerable,
                self.weaken)


class Card(CardArgs, Enum):
    ANGER = CardArgs(0, attack=6)
    BASH = CardArgs(2, attack=8, vulnerable=2)
    BASH_PLUS = CardArgs(2, attack=10, vulnerable=3)
    DEFEND = CardArgs(1, block=5)
    DEMON_FORM = CardArgs(3, exhausts=True, strength_buff=2) # is a power add card type
    DISARM = CardArgs(1, exhausts=True, enemy_strength_gain=-2)
    FLEX = CardArgs(0, strength_gain=2, strength_loss=2)
    HEAVY_BLADE = CardArgs(1, attack=14, attack_strength_multiplier=3)
    INFLAME = CardArgs(1, exhausts=True, strength_gain=2)
    INTIMIDATE = CardArgs(0, exhausts=True, weaken=1)
    IRON_WAVE = CardArgs(1, attack=5, block=5)
    LIMIT_BREAK_PLUS = CardArgs(1, strength_multiplier=2)
    PERFECTED_STRIKE = CardArgs(2, attack=6, strike_bonus=2)
    PERFECTED_STRIKE_PLUS = CardArgs(2, attack=6, strike_bonus=3)
    POMMEL_STRIKE = CardArgs(1, attack=8, draw_card=1)
    POMMEL_STRIKE_NO_DRAW = CardArgs(1, attack=8, draw_card=0)
    PUMMEL = CardArgs(1, attack=2, attack_multiplier=4, exhausts=True)
    STRIKE = CardArgs(1, attack=6)
    TWIN_STRIKE = CardArgs(1, attack=5, attack_multiplier=2)
    TWIN_STRIKE_PLUS = CardArgs(1, attack=7, attack_multiplier=2)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def is_attack(self):
        return bool(self.attack or self.strength_buff or self.strength_gain or self.strength_multiplier > 1)

    def is_defend(self):
        return bool(self.block),

    def extra_action(self, deck):
        if self.name == 'ANGER':
            deck.add_to_discards([Card.ANGER])

    def calculate_strike_bonus(self, deck):
        if self.strike_bonus == 0:
            return 0

        cards_with_strike = len(
            [c for c in deck.all_cards() if 'STRIKE' in str(c)])
        strike_bonus = (
            self.strike_bonus * cards_with_strike)
        logger.debug(
            f"cards with strike: {cards_with_strike}, strike bonus: {strike_bonus}")
        return strike_bonus


IRONCLAD_STARTER = [Card.DEFEND]*4 + [Card.STRIKE]*5 + [Card.BASH]
