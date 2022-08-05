import math
import logging
from re import S
from types import NoneType
import numpy
import sys
import matplotlib.pyplot as plt
from enum import Enum
from collections import namedtuple
import numpy.polynomial.polynomial as poly
from typing import List, Sequence, Union

logging.basicConfig(filename='sts.log', encoding='utf-8', level=logging.INFO)


class CardArgs(namedtuple('CardArgs', (
    'energy '
    'attack '
    'attack_multiplier '
    'attack_strength_multiplier '
    'block '
    'draw_card '
    'exhaustible '
    'strength_buff '
    'strength_gain '
    'strength_loss '
    'strength_multiplier '
    'strike_bonus '
        'vulnerable'))):
    def __new__(cls, energy,
                attack=0,
                attack_multiplier=1,
                attack_strength_multiplier=1,
                block=0,
                draw_card=0,
                exhaustible=False,
                strength_buff=0,
                strength_gain=0,
                strength_loss=0,
                strength_multiplier=1,
                strike_bonus=0,
                vulnerable=0):
        return super().__new__(cls, energy,
                               attack,
                               attack_multiplier,
                               attack_strength_multiplier,
                               block,
                               draw_card,
                               exhaustible,
                               strength_buff,
                               strength_gain,
                               strength_loss,
                               strength_multiplier,
                               strike_bonus,
                               vulnerable)

    def __getnewargs__(self):
        return (self.energy,
                self.attack,
                self.attack_multiplier,
                self.attack_strength_multiplier,
                self.block,
                self.draw_card,
                self.exhaustible,
                self.strength_gain,
                self.strength_buff,
                self.strength_multiplier,
                self.strike_bonus,
                self.vulnerable)


class Card(CardArgs, Enum):
    ANGER = CardArgs(0, attack=6)
    BASH = CardArgs(2, attack=8, vulnerable=2)
    DEFEND = CardArgs(1, block=5)
    DEMON_FORM = CardArgs(3, exhaustible=True, strength_buff=2)
    FLEX = CardArgs(0, strength_gain=2, strength_loss=2)
    HEAVY_BLADE = CardArgs(1, attack=14, attack_strength_multiplier=3)
    INFLAME = CardArgs(1, exhaustible=True, strength_gain=2)
    LIMIT_BREAK_PLUS = CardArgs(1, strength_multiplier=2)
    PERFECTED_STRIKE = CardArgs(2, attack=6, strike_bonus=2)
    POMMEL_STRIKE = CardArgs(1, attack=8, draw_card=1)
    POMMEL_STRIKE_NO_DRAW = CardArgs(1, attack=8, draw_card=0)
    STRIKE = CardArgs(1, attack=6)
    TWIN_STRIKE = CardArgs(1, attack=5, attack_multiplier=2)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def is_attack(self):
        return bool(self.attack or self.strength_buff or self.strength_gain or self.strength_multiplier > 1),

    def is_defend(self):
        return bool(self.block),

    def extra_action(self, deck):
        if self.name == 'ANGER':
            deck.discards.append(Card.ANGER)


IRONCLAD_STARTER = [Card.DEFEND]*4 + [Card.STRIKE]*5 + [Card.BASH]


class Deck:
    def __init__(self, cards, seed=1, shuffle=True):
        self.deck = cards.copy()
        self.discards = []
        self.hand = []
        self.exhausted = []
        numpy.random.seed(seed=seed)
        if shuffle:
            numpy.random.shuffle(self.deck)
        logging.info(f"Deck: {self.deck}")

    def _deal(self) -> Union[Card, None]:
        logging.debug(f"deal: {self}")

        if not self.deck:
            if self.discards:
                self.deck = self.discards.copy()
                self.discards = []
                logging.info(f"shuffling... {self}")
                numpy.random.shuffle(self.deck)

        if not self.deck:
            return None
        dealt = self.deck.pop(0)
        self.hand.append(dealt)
        return dealt


    def deal_multi(self, count=1) -> List[Card]:
        logging.debug(f"deal_multi: {self}")

        cards = []
        while count > 0:
            card = self._deal()
            if not card:
                return cards
            count -= 1
            cards.append(card)
        
        logging.info(f"dealt {self}")

        return cards

    def discard(self, cards):
        cards = cards.copy()
        logging.debug(f"about to discard {cards}, now {self}")
        self.discards.extend(cards)
        logging.debug(f"extended {cards}, now {self}")

        for card in cards:
            self.hand.remove(card)
            logging.debug(f"just discarded {card}, now {self}")
        logging.debug(f"discarded {cards}, now {self}")
    
    def exhaust(self, cards):
        for card in cards:
            self.hand.remove(card)
        self.exhausted.extend(cards)
    
    def all_cards(self) -> List[Card]:
        # does not include exhaust
        return self.hand + self.deck + self.discards

    def sort_hand(self, key):
        self.hand.sort(reverse=True, key=key)

    def __str__(self):
        return f"hand: {self.hand}, discards: {self.discards}, exhausted: {self.exhausted}, deck: {self.deck}"


class Monster:
    def __init__(self) -> None:
        self._damage = []
        self._turn = 0
        self._vulnerable = 0

    def begin_turn(self):
        self._damage.append(0)

    def defend(self, attack):
        self._damage[self._turn] += int(attack *
                                        (1.5 if self._vulnerable else 1.0))
        logging.debug(
            f"{self._turn}: MONSTER TAKING DAMAGE: vuln: {self._vulnerable}: {attack} -> {self._damage[self._turn]}")

    def vulnerable(self, turns):
        self._vulnerable += turns
        logging.debug(
            f"{self._turn}: MONSTER TAKING VULNERABLE:{turns} -> {self._vulnerable}")

    def end_turn(self):
        if self._vulnerable > 0:
            self._vulnerable -= 1
        self._turn += 1

    def get_damage(self):
        return self._damage


class Player:

    def __init__(self, deck: Deck, energy=3) -> None:
        self.deck = deck
        self.energy = energy

        self.block = 0
        self.blocks = []
        self.strength = 0
        self.strength_buff = 0
        self.post_strength_debuff_once = 0

    def select_card_to_play(self, energy) -> Union[Card, None]:
        # Removes selected card from hand.
        for card in self.deck.hand:
            logging.debug(f"energy: {energy} looking at card: {card} / {self.deck.hand}")

            if card.energy and energy < card.energy:
                continue
            return card
        return None

    def _play_hand(self, monster: Monster):

        def _sort_key(c: Card):
            k = (c.is_attack(),
                 c.energy if c.energy else 1000,
                 c.exhaustible,
                 c.strength_gain,
                 c.strength_multiplier,
                 c.attack)
            logging.debug(f"attack_sort_key: {c}, {k}")
            return k

        self.deck.sort_hand(_sort_key)

        energy = self.energy
        played_cards = []

        card_to_play = self.select_card_to_play(energy)
        while card_to_play:
            logging.debug(f"playing card: {card_to_play}")
            played_cards.append(card_to_play)
            energy -= card_to_play.energy
            if card_to_play.exhaustible:
                self.deck.exhaust([card_to_play])
            else:
                self.deck.discard([card_to_play])

            if card_to_play.attack:
                strike_bonus = 0
                if card_to_play.strike_bonus:
                    cards_with_strike = len(
                        [c for c in self.deck.all_cards() if 'STRIKE' in str(c)])
                    strike_bonus = (
                        card_to_play.strike_bonus * cards_with_strike)
                    logging.debug(
                        f"cards with strike: {cards_with_strike}, strike bonus: {strike_bonus}")
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
                cards = self.deck.deal_multi(card_to_play.draw_card)
                logging.info(f"drawing cards: {cards}")
                self.deck.sort_hand(_sort_key)

            card_to_play.extra_action(self.deck)

            card_to_play = self.select_card_to_play(energy)

        self.blocks.append(self.block)

        logging.debug(f"discarding remaining cards in hand: {self.deck.hand}")
        self.deck.discard(self.deck.hand)

        return played_cards

    def play_turn(self, monster: Monster):
        logging.debug("play_turn...")
        monster.begin_turn()
        self.strength += self.strength_buff
        self.block = 0
        
        self.deck.deal_multi(5)
        played_cards = self._play_hand(monster)
        logging.info(f"Played: {played_cards}")

        if self.post_strength_debuff_once:
            self.strength -= self.post_strength_debuff_once
            self.post_strength_debuff_once = 0

        monster.end_turn()
        logging.info(f"damage: {monster.get_damage()}")

    def play_game(self, monster: Monster, turns: int):
        for turn in range(turns):
            self.play_turn(monster)
        # logging.info(f"damage: {numpy.cumsum(monster.get_damage())}")
        # logging.info(f"damage: {monster.get_damage()}")


# class DefendingPlayer(Player):
#     def __init__(self, deck: Deck, energy=3) -> None:
#         super().__init__(deck, energy)

#     def _play_hand(self, hand: list, monster: Monster):

#         def _sort_key(c: Card):
#             k = (c.is_defend(),
#                  c.energy if c.energy else 1000, c.exhaustible)
#             logging.debug(f"_sort_key: {c}, {k}")
#             return k

#         hand.sort(reverse=True, key=_sort_key)

#         logging.info(f"HAND: {hand}")

#         energy = self.energy
#         played_cards = []

#         # Copy hand so that the original hand can be mutated (cards can be exhausted).
#         for card in hand.copy():
#             logging.debug(f"energy: {energy} looking at card: {card} / {hand}")

#             if card.energy and energy < card.energy:
#                 continue

#             logging.debug(f"playing card: {card}")
#             played_cards.append(card)
#             energy -= card.energy

#             self.block += card.block

#             if card.exhaustible:
#                 hand.remove(card)

#             card.extra_action(self.deck)

#         return played_cards

#     def play_turn(self, monster: Monster):
#         monster.begin_turn()
#         hand = self.deck.deal_multi(5)

#         played_cards = self._play_hand(hand, monster)
#         logging.info(f"Played: {played_cards}")

#         logging.debug(f"discarding {hand}")
#         self.deck.discard(hand)

#         monster.end_turn()
#         logging.info(f"damage: {monster.get_damage()}")

#     def play_game(self, monster: Monster, turns: int):
#         for turn in range(turns):
#             self.play_turn(monster)
#         # logging.info(f"damage: {numpy.cumsum(monster.get_damage())}")
#         # logging.info(f"damage: {monster.get_damage()}")


def get_frontloaded_damage(damage: list):
    return (damage[0] +
            damage[1]/2.0 +
            damage[2]/4.0 +
            damage[3]/8.0)


def create_scatter_plot_data(plot_data, attribute):
    trials = len(plot_data)
    plot_data = numpy.swapaxes(plot_data, 0, 1)
    scatter_data = {}
    scatter_data['turns'] = []
    scatter_data[attribute] = []
    size = []
    logging.debug(f"plot_data: {plot_data}")
    for turn in range(len(plot_data)):
        turn_attrib = plot_data[turn]
        r = range(int(min(turn_attrib)), 2+int(max(turn_attrib)))
        hist = numpy.histogram(turn_attrib, bins=r)
        for bin_count, bin in zip(*hist):
            if bin_count:
                scatter_data['turns'].append(turn)
                scatter_data[attribute].append(bin)
                size.append(bin_count/(trials/100.0))
        # if turn == 0:
        #     logging.debug(f"TURN0 hist: {hist}")
        #     logging.debug(f"TURN0 size: {size}")
        #     logging.debug(f"TURN0 scatter_data {scatter_data}")

    return scatter_data, size


def format_scaling_damage(coefs):
    scaling_damages = tuple([int(round(cc, 0)) for cc in coefs[1:]])
    while scaling_damages and not scaling_damages[-1]:
        scaling_damages = scaling_damages[:-1]
    if not scaling_damages:
        return "O(1)"

    preandpost = [('', '*n'), (' + ', '*n^2'), (' + ', '*n^3')]
    ret = ''
    for i in range(len(scaling_damages)):
        pp = preandpost[i]
        ret += f"{pp[0]}{scaling_damages[i]}{pp[1]}"
    return f"O({ret})"


def curve_fit(x, y):
    pret = poly.polyfit(x, y, 2, full=True)
    coefs = pret[0]
    residuals = pret[1][0]
    fit = poly.polyval(x, coefs)
    return coefs, residuals, fit


def main():
    if len(sys.argv) > 1:
        cards = eval(sys.argv[1])
    else:
        cards = IRONCLAD_STARTER

    turns = 20
    trials = 1000
    cum_damage = []
    damage = []
    block = []
    for trial in range(trials):
        player = Player(Deck(cards, seed=trial))
        monster = Monster()
        player.play_game(monster, turns)
        damage.append(monster.get_damage())
        cum_damage.append(numpy.cumsum(monster.get_damage()))
        block.append(player.blocks)

    logging.debug(f"damage: {damage}")
    logging.debug(f"block: {block}")

    average_damage = numpy.average(damage, axis=0)

    log_average_damage = [math.log(d, 2) for d in average_damage]
    turns_after_first_deck = 2+int(len(cards) / 5)
    x = list(range(turns))
    x_after_first_deck = x[turns_after_first_deck:]

    print("curvefit")
    coefs, residuals, ffit = curve_fit(
        x_after_first_deck, average_damage[turns_after_first_deck:])

    print("curvefit log")
    log_coefs, log_residuals, log_ffit = curve_fit(
        x_after_first_deck, log_average_damage[turns_after_first_deck:])

    frontloaded_damage = get_frontloaded_damage(average_damage)
    if abs(residuals) >= 100:
        scaling_damage = f"O({log_coefs[1]:.2f}*2^n)"
    else:
        scaling_damage = format_scaling_damage(coefs)

    print(f"average: {average_damage}")
    print(f"log_average: {log_average_damage}")
    print(f"FRONTLOADED DAMAGE: {frontloaded_damage:.2f}")
    print(
        f"SCALING DAMAGE: coefs: {coefs}, log: {log_coefs}, {scaling_damage}")
    print(f"RESIDUALS: r: {residuals}, rlog: {log_residuals}")

    fig, (ax, ax1) = plt.subplots(ncols=2)  # type: ignore
    if abs(residuals) < 100:
        ax.plot(x_after_first_deck, ffit, color='green')
    else:
        ax.plot(x_after_first_deck, [math.pow(2, y)
                                     for y in log_ffit], color='purple')

    ax.scatter(x, average_damage, s=4, color='red', marker="_")
    if abs(residuals) > 100:
        ax.scatter(x, log_average_damage, s=4, color='purple', marker="_")

    damage_scatter_data, size = create_scatter_plot_data(damage, 'damage')
    logging.debug(f"scatter_data: {damage_scatter_data}, {size}")
    ax.scatter('turns', 'damage', s=size, data=damage_scatter_data)

    block_scatter_data, size = create_scatter_plot_data(block, 'block')
    ax1.scatter('turns', 'block', s=size, data=block_scatter_data)

    ax.set_title(
        f'DAMAGE: [{frontloaded_damage:.2f}hp, {scaling_damage}]', loc='right', fontsize=8)

    ax.set_xlabel('turn')
    ax.set_ylabel('damage')

    ax1.set_xlabel('turn')
    ax1.set_ylabel('block')
    if len(sys.argv) > 1:
        plt.suptitle(f'{sys.argv[1]}')
    else:
        plt.suptitle("IRONCLAD BASE")

    plt.show()


if __name__ == "__main__":
    main()
