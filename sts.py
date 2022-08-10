import argparse
import logging
import logging.config
import math
import sys
from collections import namedtuple
from typing import Sequence

import matplotlib.pyplot as plt
import numpy
import numpy.polynomial.polynomial as poly
import numpy.typing as npt

from card import Card
from deck import Deck
from monster import JawWorm, Monster
from player import AttackingPlayer, DefendingPlayer

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
turn_logger = logging.getLogger("turns")
logger = logging.getLogger("sts")


def get_frontloaded_damage(damage: list, scale=True):
    fld = 0.0
    scaling = 1.0
    for ix in range(min(len(damage), 4)):
        fld += damage[ix] * (scaling if scale else 1.0)
        scaling /= 2.0
    print(f"FRONTLOADED DAMAGE: {fld:.2f}")
    return fld


def create_scatter_plot_data(plot_data, attribute):
    trials = len(plot_data)
    plot_data = numpy.swapaxes(plot_data, 0, 1)
    scatter_data = {}
    scatter_data['turns'] = []
    scatter_data[attribute] = []
    attributes_by_turn = []
    size = []
    logging.debug(f"plot_data: {plot_data}")
    hists = []
    sizes_by_attribute = []
    for turn in range(len(plot_data)):
        size_by_attribute = {}
        turn_attrib = plot_data[turn]
        r = range(int(min(turn_attrib)), 2+int(max(turn_attrib)))
        hist = numpy.histogram(turn_attrib, bins=r)
        for bin_count, bin in zip(*hist):
            if bin_count:
                scatter_data['turns'].append(turn)
                scatter_data[attribute].append(bin)
                s = bin_count/(trials/100.0)
                size_by_attribute[bin] = s
                hists.append(hist)
                size.append(s)
        sizes_by_attribute.append(size_by_attribute)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"TURN hist: {hist}")
            logger.debug(f"TURN size: {size}")
            logger.debug(f"TURN scatter_data {scatter_data}")

    logging.debug(f"scatter_data: {scatter_data}, {size}")

    return scatter_data, size, sizes_by_attribute


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
    pret = poly.polyfit(x, y, 1, full=True)
    coefs = pret[0]
    residuals = pret[1][0]
    fit = poly.polyval(x, coefs)
    return coefs, residuals, fit


def plot_one_attribute(ax, x, data, size_by_turn, color):
    sizes = []
    for i in range(len(data)):
        sizes.append(size_by_turn[i][data[i]])
    ax.scatter(x[0:len(data)], data, s=sizes, color=color)


def pad_to_dense(M) -> list:
    """Appends the minimal required amount of zeroes at the end of each 
     array in the jagged array `M`, such that `M` loses its jagedness."""

    maxlen = max(len(r) for r in M)

    Z = numpy.zeros((len(M), maxlen))
    for enu, row in enumerate(M):
        Z[enu, :len(row)] += row
    return Z.tolist()


class TrialStats:
    def __init__(self):

        # TODO(sng): convert to numpy arrays
        self.monster_damage = []
        self.cum_monster_damage = []
        self.player_block = []

    def add_player_block(self, block):
        self.player_block.append(block)

    def add_monster_damage(self, damage: Sequence):
        self.monster_damage.append(damage)

    def finish_trials(self):
        self.monster_damage = pad_to_dense(self.monster_damage)
        self.player_block = pad_to_dense(self.player_block)

        self.average_monster_damage = numpy.average(
            self.monster_damage, axis=0)
        self.cum_monster_damage = numpy.sum(self.average_monster_damage)
        self.log_average_monster_damage = [
            math.log(d, 2) for d in self.average_monster_damage]
    
        self.average_player_block = numpy.average(self.player_block, axis=0)
        logger.debug(f"damage: {self.monster_damage}")
        logger.debug(f"block: {self.player_block}")
        print(f"average_damage: {self.average_monster_damage}")
        print(f"cum_damage: {self.cum_monster_damage}")
        print(f"average_block: {self.average_player_block}")


TurnInfo = namedtuple("TurnInfo", "TotalDamage CardsPlayed Damages")


class CombatLog:
    def __init__(self) -> None:
        self.best_block = [0, None]
        self.worst_block = [sys.maxsize, None]

        self.best_attack = TurnInfo(
            TotalDamage=0, CardsPlayed=None, Damages=[])
        self.worst_attack = TurnInfo(
            TotalDamage=sys.maxsize, CardsPlayed=None, Damages=[])

    def add_combat(self, total_damage: int, combat: TurnInfo):
        if total_damage > self.best_attack.TotalDamage:
            self.best_attack = combat
        if total_damage < self.worst_attack.TotalDamage:
            self.worst_attack = combat

    def add_block(self, total_block, cards_played):
        if total_block > self.best_block[0]:
            self.best_block = [total_block, cards_played]
        if total_block < self.worst_block[0]:
            self.worst_block = [total_block, cards_played]

    def finish(self):
        print(f"BEST ATTACK: {self.best_attack}")
        print(f"WORST ATTACK: {self.worst_attack}")
        print(f"BEST BLOCK: {self.best_block}")
        print(f"WORST BLOCK: {self.worst_block}")

def get_scaling_damage(coefs, log_coefs, residuals):
    if abs(residuals) >= 100:
        return f"O({log_coefs[1]:.2f}*2^n)"
    else:
        return format_scaling_damage(coefs)

def get_damage_stats(turns_after_first_deck, x_after_first_deck, trial_stats):
    print("curvefit")
    coefs, residuals, ffit = curve_fit(
        x_after_first_deck, trial_stats.average_monster_damage[turns_after_first_deck:])

    # logging.debug(f"residuals: r: {residuals}, rlog: {log_residuals}")

    if abs(residuals) >= 100:
        print("curvefit log")
        log_coefs, log_residuals, log_ffit = curve_fit(
            x_after_first_deck, trial_stats.log_average_monster_damage[turns_after_first_deck:])
        ffit = [math.pow(2, y) for y in log_ffit]
        scaling = f"O({log_coefs[1]:.2f}*2^n)"
    else:
        scaling = format_scaling_damage(coefs)

    return ffit, scaling 


def main():
    logging.debug(f"starting...")
    logging.info(f"info starting...")

    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'cards', nargs='?', help='list of cards (defaults to Ironclad base set)')
    argparser.add_argument(
        '--strategy', help='player strategy (default: AttackingPlayer)', default="AttackingPlayer")
    argparser.add_argument(
        '--trials', help='number of trials', type=int, default=10000)
    argparser.add_argument(
        '--turns', help='number of turns', type=int, default=20)
    argparser.add_argument(
        '--monster', help='monster to fight', default='Monster')
    args = argparser.parse_args()
    strategy = eval(args.strategy)
    cards = eval(args.cards)
    monster_factory = eval(args.monster)

    trial_stats = TrialStats()
    combat_log = CombatLog()
    turns = args.turns
    trials = args.trials
    for trial in range(trials):
        player = strategy(Deck(cards, seed=trial))
        monster = monster_factory()
        logger.debug(f"monster: {monster}")
        player.play_game(monster, turns)
        trial_stats.add_monster_damage(monster.get_damage())
        trial_stats.add_player_block(player.blocks)
        total_block = numpy.sum(player.blocks)
        total_damage = numpy.sum(monster.get_damage())
        combat_log.add_combat(total_damage, TurnInfo(
            total_damage, player.played_cards, monster.get_damage()))
        combat_log.add_block(total_block, player.played_cards)
        if trial % 100 == 0:
            print(".", end='', file=sys.stderr, flush=True)
    print("", file=sys.stderr)
    combat_log.finish()
    trial_stats.finish_trials()

    fig, (ax0, ax1) = plt.subplots(ncols=2, figsize=(10, 8))  # type: ignore

    turns_after_first_deck = 2 * int(len(cards) / 5)
    if len(trial_stats.average_monster_damage) - turns_after_first_deck < 2:
        turns_after_first_deck = 0
    x = list(range(len(trial_stats.average_monster_damage)))
    x_after_first_deck = x[turns_after_first_deck:]

    print("curvefit")
    coefs, residuals, ffit = curve_fit(
        x_after_first_deck, trial_stats.average_monster_damage[turns_after_first_deck:])

    print("curvefit log")
    log_coefs, log_residuals, log_ffit = curve_fit(
        x_after_first_deck, trial_stats.log_average_monster_damage[turns_after_first_deck:])
    logging.debug(f"residuals: r: {residuals}, rlog: {log_residuals}")

    frontloaded_damage = get_frontloaded_damage(trial_stats.average_monster_damage)

    curve_fit_data, scaling_damage = get_damage_stats(turns_after_first_deck, x_after_first_deck, trial_stats)
    print(f"SCALING DAMAGE: coefs: {coefs}, log: {log_coefs}, {scaling_damage}")

    ax0.plot(x_after_first_deck, curve_fit_data, color='gray')

    damage_scatter_data, size, damage_by_size_by_turn = create_scatter_plot_data(
        trial_stats.monster_damage, 'damage')
    ax0.scatter('turns', 'damage', s=size, data=damage_scatter_data)
    ax0.plot(trial_stats.average_monster_damage,
             linestyle='dotted', linewidth=1, color='grey')

    logging.debug(
        f"best damage {combat_log.best_attack.Damages}, {size}, {damage_by_size_by_turn}")

    plot_one_attribute(ax0, x, combat_log.best_attack.Damages,
                       damage_by_size_by_turn, 'lime')
    plot_one_attribute(ax0, x, combat_log.worst_attack.Damages,
                       damage_by_size_by_turn, 'lightcoral')

    block_scatter_data, size, _ = create_scatter_plot_data(trial_stats.player_block, 'block')
    ax1.scatter('turns', 'block', s=size, data=block_scatter_data)
    # ax1.scatter(x, trial_stats.player_block, s=8, color='grey', marker="_")
    ax1.plot(trial_stats.average_player_block, linestyle='dotted', linewidth=1, color='grey')

    ax0.set_title(
        f'total: {trial_stats.cum_monster_damage:.2f} ({combat_log.worst_attack.TotalDamage} to {combat_log.best_attack.TotalDamage}) frontload: {frontloaded_damage:.2f}hp scaling: {scaling_damage}', loc='right', fontsize=8)

    ax0.set_xlabel('turn')
    ax0.set_ylabel('damage')

    ax1.set_xlabel('turn')
    ax1.set_ylabel('block')
    ax1.set_title(
        f'avg block: {numpy.average(trial_stats.average_player_block):.2f}', loc='right', fontsize=8)
    if len(sys.argv) > 1:
        plt.suptitle(f'strategy: {args.strategy}\n{args.cards}')
    else:
        plt.suptitle("IRONCLAD BASE")

    plt.show()


if __name__ == "__main__":
    main()
