import logging
from typing import Union

from card import Card
from character import Character
from deck import Deck
from monster import Monster
from csv_logger import CsvLogger
import fastai_sts
import numpy
import random
import aidata

logger = logging.getLogger("turns").getChild(__name__)
csv_logger = CsvLogger("FINAL_HP,GAME,N_TURN,N_PLAY,PLAY," + aidata.CONT_DATA)

HAND_CARDS = [Card.STRIKE, Card.BASH, Card.DEFEND]

class Player(Character):

    def __init__(self, deck: Deck, energy: int = 3, hp: int = 72) -> None:
        super().__init__(hp=hp)
        self.deck = deck
        self.energy = energy
        self.blocks = []
        self.played_cards = []
        self.post_strength_debuff_once = 0

    @staticmethod
    def _sort_key(c: Card):
        pass

    @staticmethod
    def attack_sort_key(c: Card):
        k = (c.energy == 0,
             c.is_attack(),
             c.strength_gain,
             c.strength_multiplier,
             c.energy if c.energy else 1000,  # remove else
             c.exhausts,
             c.attack)
        logger.debug(f"attack_sort_key: {c}, {k}")
        return k

    @staticmethod
    def defend_sort_key(c: Card):
        k = (c.energy == 0,
             not c.is_attack(),
             c.energy if c.energy else 1000,
             c.block)
        logger.debug(f"defend_sort_key: {c}, {k}")
        return k

    def select_card_to_play(self, energy, monster: Monster) -> Union[Card, None]:
        for card in self.deck.hand:
            if card.energy > energy:
                continue
            if self.block >= monster.attack() and card.block > 0:
                logger.info(
                    f"!!skipping {card} due to sufficient block: {self.block} >= {monster.planned_damage}")
                # continue

            return card

        return None

    def _sort_hand(self):
        self.deck.sort_hand(self._sort_key)
        logger.debug(f"Sorted: {self.deck.hand}")

    def _play_hand(self, monster: Monster):
        self._sort_hand()

        energy = self.energy
        played_cards = []
        logger.info(f"incoming attack: {monster.attack()}")
        card_to_play = self.select_card_to_play(energy, monster)
        while card_to_play:
            if not monster.hp:
                return played_cards
            logger.debug(f"playing card: {card_to_play}")
            # print(f"{self.deck.hand}: {self.deck.hand.count(Card.STRIKE)}")
            csv_logger.play_card(
                (card_to_play.name, energy, self.hp, self.block,
                 monster.hp, monster.attack(), monster.block, monster.get_vulnerable(),
                 self.deck.hand.count(Card.STRIKE), self.deck.hand.count(Card.BASH)))

            played_cards.append(card_to_play)
            energy -= card_to_play.energy
            if card_to_play.exhausts:
                self.deck.exhaust([card_to_play])
            else:
                self.deck.discard_from_hand([card_to_play])

            if card_to_play.attack:
                strike_bonus = card_to_play.calculate_strike_bonus(self.deck)
                damage = (card_to_play.attack_multiplier *
                          (card_to_play.attack + strike_bonus + self.strength * card_to_play.attack_strength_multiplier))
                monster.defend(damage)

            if card_to_play.vulnerable:
                monster.vulnerable(card_to_play.vulnerable)

            monster.strength += card_to_play.enemy_strength_gain
            self.block += card_to_play.block
            self.strength_buff += card_to_play.strength_buff
            self.strength += card_to_play.strength_gain
            self.post_strength_debuff_once += card_to_play.strength_loss
            self.strength *= card_to_play.strength_multiplier
            if card_to_play.draw_card:
                # store card for logging only
                cards = self.deck.deal(card_to_play.draw_card)
                logger.info(f"drawing cards: {cards}")
                self.deck.sort_hand(self._sort_key)

            card_to_play.extra_action(self.deck)
            # QUIT IF MONSTER DEAD
            card_to_play = self.select_card_to_play(energy, monster)

        self.blocks.append(self.block)

        self.deck.discard_from_hand(self.deck.hand)

        return played_cards

    def play_turn(self, monster: Monster):
        logger.debug("play_turn...")
        csv_logger.next_turn()
        self.block = 0

        self.deck.deal(5)
        self.played_cards.append(self._play_hand(monster))
        logger.info(f"Played: {self.played_cards[-1]}")
        if monster.hp:
            attack = monster.attack()  # monster.isAttacking()
            if attack:
                self.defend(attack)
        if self.post_strength_debuff_once:
            self.strength -= self.post_strength_debuff_once
            self.post_strength_debuff_once = 0

        monster.end_turn()
        self.end_turn()

    def play_game(self, monster: Monster, turns: int):
        logger.info(
            f"GAME START player.hp: {self.hp}, monster.hp: {monster.hp}")
        for turn in range(turns):
            logger.info(f"***** TURN {turn} ******")
            self.play_turn(monster)
            if not monster.hp or not self.hp:
                break
        logger.info(
            f"GAME END player.hp: {self.hp} monster.hp: {monster.hp}, damage: {monster.get_damage()}")
        csv_logger.end_game(self.hp)


class DefendingPlayer(Player):
    @staticmethod
    def _sort_key(c: Card):
        return (Player.defend_sort_key(c), Player.attack_sort_key(c))


class AttackingPlayer(Player):
    @staticmethod
    def _sort_key(c: Card):
        return (Player.attack_sort_key(c), Player.defend_sort_key(c))


class AIPlayer(Player):
    _m = None

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        if not AIPlayer._m:
            AIPlayer._m = fastai_sts.setup_model()

    def _sort_hand(self):
        self.deck.sort_hand(None)

    def select_card_to_play(self, energy, monster: Monster) -> Union[Card, None]:
        uniq_cards = set(card for card in self.deck.hand if card.energy <= energy)
        if not uniq_cards:
            return None
        data = {
            "PLAY": [c.name for c in uniq_cards],
            "ENERGY": energy,
            "PLAYER_HP": self.hp,
            "PLAYER_BLOCK": self.block,
            "MONSTER_HP": monster.hp,
            "MONSTER_ATTACK": monster.attack(),
            "MONSTER_BLOCK": monster.block,
            "MONSTER_VULNERABLE": monster.get_vulnerable(),
        }
        hand_dict = { k:v for (k, v) in [(f"HAND_{c.name}", self.deck.hand.count(c)) for c in HAND_CARDS]}
        data.update(hand_dict)
        logger.debug(f"data {data}")
        
        ps = fastai_sts.predict(data, self._m)
        best_cards = [x[1] for x in zip(ps, uniq_cards) if x[0] == min(ps)]
        best_card = random.choice(list(best_cards))
        logger.debug(f"best_card --> {list(zip(ps, uniq_cards))} --> {list(best_cards)} --> {best_card}")
        return best_card


class RandomPlayer(Player):
    def _sort_hand(self):
        self.deck.sort_hand(None)
        logger.info(f"Sorted: {self.deck.hand}")
