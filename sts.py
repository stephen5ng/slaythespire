import argparse
import logging
import logging.config
import math
import sys
from collections import namedtuple

import matplotlib.pyplot as plt
import numpy
import numpy.polynomial.polynomial as poly

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
        # if turn == 0:
        #     logging.debug(f"TURN0 hist: {hist}")
        #     logging.debug(f"TURN0 size: {size}")
        #     logging.debug(f"TURN0 scatter_data {scatter_data}")

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


def pad_to_dense(M):
    """Appends the minimal required amount of zeroes at the end of each 
     array in the jagged array `M`, such that `M` looses its jagedness."""

    maxlen = max(len(r) for r in M)

    Z = numpy.zeros((len(M), maxlen))
    for enu, row in enumerate(M):
        Z[enu, :len(row)] += row
    return Z


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

    turns = args.turns
    trials = args.trials
    cum_damage = []
    damage = []
    block = []
    TurnInfo = namedtuple("TurnInfo", "TotalDamage CardsPlayed Damages")
    best_attack = TurnInfo(TotalDamage=0, CardsPlayed=None, Damages=[])
    worst_attack = TurnInfo(TotalDamage=sys.maxsize,
                            CardsPlayed=None, Damages=[])
    best_block = [0, None]
    worst_block = [sys.maxsize, None]
    for trial in range(trials):
        player = strategy(Deck(cards, seed=trial))
        monster = monster_factory()
        logger.debug(f"monster: {monster}")
        player.play_game(monster, turns)
        damage.append(monster.get_damage())
        cum_damage.append(numpy.cumsum(monster.get_damage()))
        block.append(player.blocks)
        total_block = numpy.sum(player.blocks)
        total_damage = numpy.sum(monster.get_damage())
        # total_damage = get_frontloaded_damage(monster.get_damage())
        # print(f"checking: {total_damage}, {best_play[0]}")
        if total_damage > best_attack.TotalDamage:
            best_attack = TurnInfo(
                total_damage, player.played_cards, monster.get_damage())
        if total_damage < worst_attack.TotalDamage:
            worst_attack = TurnInfo(
                total_damage, player.played_cards, monster.get_damage())
        if total_block > best_block[0]:
            best_block = [total_block, player.played_cards]
        if total_block < worst_block[0]:
            worst_block = [total_block, player.played_cards]
        if trial % 100 == 0:
            print(".", end='', file=sys.stderr, flush=True)
    print("", file=sys.stderr)
    logger.debug(f"damage: {damage}")
    logger.debug(f"block: {block}")
    print(f"BEST ATTACK: {best_attack}")
    print(f"WORST ATTACK: {worst_attack}")
    print(f"BEST BLOCK: {best_block}")
    print(f"WORST BLOCK: {worst_block}")
    damage = pad_to_dense(damage)
    block = pad_to_dense(block)

    average_damage = numpy.average(damage, axis=0)
    cum_damage = numpy.sum(average_damage)
    average_block = numpy.average(block, axis=0)
    print(f"average damage {average_damage}")
    log_average_damage = [math.log(d, 2) for d in average_damage]
    turns_after_first_deck = 2 * int(len(cards) / 5)
    if len(average_damage) - turns_after_first_deck < 2:
        turns_after_first_deck = 0
    x = list(range(len(average_damage)))
    x_after_first_deck = x[turns_after_first_deck:]

    print("curvefit")
    coefs, residuals, ffit = curve_fit(
        x_after_first_deck, average_damage[turns_after_first_deck:])

    print("curvefit log")
    log_coefs, log_residuals, log_ffit = curve_fit(
        x_after_first_deck, log_average_damage[turns_after_first_deck:])
    logging.debug(f"residuals: r: {residuals}, rlog: {log_residuals}")

    frontloaded_damage = get_frontloaded_damage(average_damage)
    if abs(residuals) >= 100:
        scaling_damage = f"O({log_coefs[1]:.2f}*2^n)"
    else:
        scaling_damage = format_scaling_damage(coefs)

    print(f"average_damage: {average_damage}")
    print(f"cum_damage: {cum_damage}")
    # print(f"log_average: {log_average_damage}")
    print(f"average_block: {average_block}")
    print(f"FRONTLOADED DAMAGE: {frontloaded_damage:.2f}")
    print(
        f"SCALING DAMAGE: coefs: {coefs}, log: {log_coefs}, {scaling_damage}")

    fig, (ax0, ax1) = plt.subplots(ncols=2, figsize=(10, 8))  # type: ignore
    curve_fit_data = ffit if abs(residuals) < 100 else [math.pow(2, y)
                                                        for y in log_ffit]
    ax0.plot(x_after_first_deck, curve_fit_data, color='gray')
    # ax0.scatter(x, log_average_damage, s=4, color='purple', marker="_")

    damage_scatter_data, size, damage_by_size_by_turn = create_scatter_plot_data(
        damage, 'damage')
    logging.debug(f"scatter_data: {damage_scatter_data}, {size}")
    ax0.scatter('turns', 'damage', s=size, data=damage_scatter_data)
    # ax0.scatter(x, average_damage, s=4, color='gray', marker="_")
    ax0.plot(average_damage, linestyle='dotted', linewidth=1, color='grey')

    logging.debug(
        f"best damage {best_attack.Damages}, {size}, {damage_by_size_by_turn}")

    plot_one_attribute(ax0, x, best_attack.Damages,
                       damage_by_size_by_turn, 'lime')
    plot_one_attribute(ax0, x, worst_attack.Damages,
                       damage_by_size_by_turn, 'lightcoral')

    block_scatter_data, size, _ = create_scatter_plot_data(block, 'block')
    ax1.scatter('turns', 'block', s=size, data=block_scatter_data)
    # ax1.scatter(x, average_block, s=8, color='grey', marker="_")
    ax1.plot(average_block, linestyle='dotted', linewidth=1, color='grey')

    ax0.set_title(
        f'total: {cum_damage:.2f} ({worst_attack.TotalDamage} to {best_attack.TotalDamage}) frontload: {frontloaded_damage:.2f}hp scaling: {scaling_damage}', loc='right', fontsize=8)

    ax0.set_xlabel('turn')
    ax0.set_ylabel('damage')

    ax1.set_xlabel('turn')
    ax1.set_ylabel('block')
    ax1.set_title(
        f'avg block: {numpy.average(average_block):.2f}', loc='right', fontsize=8)
    if len(sys.argv) > 1:
        plt.suptitle(f'strategy: {args.strategy}\n{args.cards}')
    else:
        plt.suptitle("IRONCLAD BASE")

    plt.show()


if __name__ == "__main__":
    main()
