import logging
from typing import Union

from card import Card
from deck import Deck
from monster import Monster

logger = logging.getLogger("turns").getChild(__name__)

class Player:

    def __init__(self, deck: Deck, energy: int = 3) -> None:
        self.deck = deck
        self.energy = energy
        self.block = 0
        self.blocks = []
        self.played_cards = []
        self.strength = 0
        self.strength_buff = 0
        self.post_strength_debuff_once = 0
        self.hp = 70

    @staticmethod
    def _sort_key(c: Card):
        pass

    @staticmethod
    def attack_sort_key(c: Card):
        k = (c.is_attack(),
             c.strength_gain,
             c.strength_multiplier,
             c.energy if c.energy else 1000,
             c.exhausts,
             c.attack)
        # logger.debug(f"attack_sort_key: {c}, {k}")
        return k

    @staticmethod
    def defend_sort_key(c: Card):
        k = (not c.is_attack(),
             c.energy if c.energy else 1000,
             c.block)
        # logger.debug(f"defend_sort_key: {c}, {k}")
        return k

    def defend(self, attack_damage):
        # print(f"defend: {attack_damage}, {self.block}")
        if attack_damage <= self.block:
            self.block -= attack_damage
            return
        self.hp -= (attack_damage - self.block)
        self.block = 0
        logger.debug(
            f"taking damge {attack_damage}, block: {self.block}, hp: {self.hp}")

    def select_card_to_play(self, energy) -> Union[Card, None]:
        for card in self.deck.hand:
            # if len(self.played_cards) < 5 and card is Card.BASH:
            #     continue

            # logger.debug(
            #     f"energy: {energy} looking at card: {card} / {self.deck.hand}")

            if card.energy and energy < card.energy:
                continue
            return card
        return None

    def _play_hand(self, monster: Monster):
        self.deck.sort_hand(self._sort_key)

        energy = self.energy
        played_cards = []

        card_to_play = self.select_card_to_play(energy)
        while card_to_play:
            logger.debug(f"playing card: {card_to_play}")
            played_cards.append(card_to_play)
            energy -= card_to_play.energy
            if card_to_play.exhausts:
                self.deck.exhaust([card_to_play])
            else:
                self.deck.discard([card_to_play])

            if card_to_play.attack:
                strike_bonus = card_to_play.calculate_strike_bonus(self.deck)
                damage = (card_to_play.attack_multiplier *
                          (card_to_play.attack + strike_bonus + self.strength * card_to_play.attack_strength_multiplier))
                monster.defend(damage)

            if card_to_play.vulnerable:
                monster.vulnerable(card_to_play.vulnerable)

            self.block += card_to_play.block
            self.strength_buff += card_to_play.strength_buff
            self.strength += card_to_play.strength_gain
            self.post_strength_debuff_once += card_to_play.strength_loss
            self.strength *= card_to_play.strength_multiplier
            if card_to_play.draw_card:
                cards = self.deck.deal(card_to_play.draw_card)
                logger.info(f"drawing cards: {cards}")
                self.deck.sort_hand(self._sort_key)

            card_to_play.extra_action(self.deck)

            card_to_play = self.select_card_to_play(energy)

        self.blocks.append(self.block)

        self.deck.discard(self.deck.hand)

        return played_cards

    def play_turn(self, monster: Monster):
        logger.debug("play_turn...")
        monster.begin_turn()
        self.strength += self.strength_buff
        self.block = 0

        self.deck.deal(5)
        self.played_cards.append(self._play_hand(monster))
        logger.info(f"Played: {self.played_cards[-1]}")

        attack = monster.attack()
        if attack:
            self.defend(attack)
        if self.post_strength_debuff_once:
            self.strength -= self.post_strength_debuff_once
            self.post_strength_debuff_once = 0

        monster.end_turn()
        logger.info(f"damage: {monster.get_damage()}")

    def play_game(self, monster: Monster, turns: int):
        for turn in range(turns):
            self.play_turn(monster)
        # logger.info(f"damage: {numpy.cumsum(monster.get_damage())}")
        # logger.info(f"damage: {monster.get_damage()}")


class DefendingPlayer(Player):
    @staticmethod
    def _sort_key(c: Card):
        return (Player.defend_sort_key(c), Player.attack_sort_key(c))


class AttackingPlayer(Player):
    @staticmethod
    def _sort_key(c: Card):
        return (Player.attack_sort_key(c), Player.defend_sort_key(c))
