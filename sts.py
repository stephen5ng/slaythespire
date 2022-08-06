import logging
import math
import sys
from collections import namedtuple
from enum import Enum
from re import S
from types import NoneType
from typing import List, Sequence, Union

import matplotlib.pyplot as plt
import numpy
import numpy.polynomial.polynomial as poly

from card import IRONCLAD_STARTER
from card import Card

logging.basicConfig(filename='sts.log', encoding='utf-8', level=logging.INFO)


class Deck:
    def __init__(self, cards, seed=1, shuffle=True):
        self._deck = cards.copy()
        self._discards = []
        self._hand = []
        self._exhausted = []
        numpy.random.seed(seed=seed)
        if shuffle:
            numpy.random.shuffle(self._deck)
        logging.info(f"Deck: {self._deck}")

    def _deal(self) -> Union[Card, None]:
        logging.debug(f"deal: {self}")

        if not self._deck:
            if self._discards:
                self._deck = self._discards.copy()
                self._discards = []
                logging.info(f"shuffling... {self}")
                numpy.random.shuffle(self._deck)

        if not self._deck:
            return None
        dealt = self._deck.pop(0)
        self._hand.append(dealt)
        return dealt

    def deal(self, count=1) -> List[Card]:
        logging.debug(f"deal: {self}")

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
        logging.debug(f"discarding {cards} from {self}")
        self.add_to_discards(cards)

        for card in cards:
            self._hand.remove(card)

    def add_to_discards(self, cards):
        logging.debug(f"add_to_discard {cards} for {self}")
        self._discards.extend(cards)

    def exhaust(self, cards):
        for card in cards:
            self._hand.remove(card)
        self._exhausted.extend(cards)

    def all_cards(self) -> List[Card]:
        # Does not include exhaust
        return self._hand + self._deck + self._discards

    def sort_hand(self, key):
        self._hand.sort(reverse=True, key=key)
        logging.debug(f"SORTED {self._hand}")

    def __str__(self):
        return f"hand: {self._hand}, discards: {self._discards}, exhausted: {self.exhausted}, deck: {self._deck}"

    def get_deck(self):
        return self._deck.copy()

    def get_discards(self):
        return self._discards.copy()

    def get_exhausted(self):
        return self._exhausted.copy()

    def get_hand(self):
        return self._hand.copy()

    deck = property(get_deck)
    discards = property(get_discards)
    exhausted = property(get_exhausted)
    hand = property(get_hand)


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

    def __init__(self, deck: Deck, energy: int = 3) -> None:
        self.deck = deck
        self.energy = energy

        self.block = 0
        self.blocks = []
        self.played_cards = []
        self.strength = 0
        self.strength_buff = 0
        self.post_strength_debuff_once = 0
        
    @staticmethod
    def attack_sort_key(c: Card):
        k = (c.is_attack(),
             c.energy if c.energy else 1000,
             c.exhaustible,
             c.strength_gain,
             c.strength_multiplier,
             c.attack)
        logging.debug(f"attack_sort_key: {c}, {k}")
        return k

    @staticmethod
    def defend_sort_key(c: Card):
        k = (not c.is_attack(),
             c.energy if c.energy else 1000,
             c.block)
        logging.debug(f"defend_sort_key: {c}, {k}")
        return k

    def select_card_to_play(self, energy) -> Union[Card, None]:
        for card in self.deck.hand:
            logging.debug(
                f"energy: {energy} looking at card: {card} / {self.deck.hand}")

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
            logging.debug(f"playing card: {card_to_play}")
            played_cards.append(card_to_play)
            energy -= card_to_play.energy
            if card_to_play.exhaustible:
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
                logging.info(f"drawing cards: {cards}")
                self.deck.sort_hand(self._sort_key)

            card_to_play.extra_action(self.deck)

            card_to_play = self.select_card_to_play(energy)

        self.blocks.append(self.block)

        self.deck.discard(self.deck.hand)

        return played_cards

    def play_turn(self, monster: Monster):
        logging.debug("play_turn...")
        monster.begin_turn()
        self.strength += self.strength_buff
        self.block = 0

        self.deck.deal(5)
        self.played_cards.append(self._play_hand(monster))
        logging.info(f"Played: {self.played_cards[-1]}")

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


class DefendingPlayer(Player):
    @staticmethod
    def _sort_key(c: Card):
        return (Player.defend_sort_key(c), Player.attack_sort_key(c))


class AttackingPlayer(Player):
    @staticmethod
    def _sort_key(c: Card):
        return (Player.attack_sort_key(c), Player.defend_sort_key(c))


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
    trials = 10000
    cum_damage = []
    damage = []
    block = []
    best_attack = [0, None]
    worst_attack = [sys.maxsize, None]
    best_block = [0, None]
    worst_block = [sys.maxsize, None]
    for trial in range(trials):
        player = AttackingPlayer(Deck(cards, seed=trial))
        monster = Monster()
        player.play_game(monster, turns)
        damage.append(monster.get_damage())
        cum_damage.append(numpy.cumsum(monster.get_damage()))
        block.append(player.blocks)
        total_block = numpy.sum(player.blocks)
        total_damage = numpy.sum(monster.get_damage())
        # print(f"checking: {total_damage}, {best_play[0]}")
        if total_damage > best_attack[0]:
            best_attack = [total_damage, player.played_cards]
        if total_damage < worst_attack[0]:
            worst_attack = [total_damage, player.played_cards]
        if total_block > best_block[0]:
            best_block = [total_block, player.played_cards]
        if total_block < worst_block[0]:
            worst_block = [total_block, player.played_cards]

    logging.debug(f"damage: {damage}")
    logging.debug(f"block: {block}")
    print(f"BEST ATTACK: {best_attack}")
    print(f"WORST ATTACK: {worst_attack}")
    print(f"BEST BLOCK: {best_block}")
    print(f"WORST BLOCK: {worst_block}")
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
