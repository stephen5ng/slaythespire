import argparse
import logging
import math
import sys

import matplotlib.pyplot as plt
import numpy
import numpy.polynomial.polynomial as poly

from deck import Deck

logging.basicConfig(filename='sts.log', encoding='utf-8', level=logging.INFO)


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
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'cards', nargs='?', help='list of cards (defaults to Ironclad base set)')
    argparser.add_argument(
        '--strategy', help='player strategy (default: AttackingPlayer)', default="AttackingPlayer")
    argparser.add_argument(
        '--trials', help='number of trials', type=int, default=10000)
    argparser.add_argument(
        '--turns', help='number of turns', type=int, default=20)
    args = argparser.parse_args()
    strategy = eval(args.strategy)
    cards = eval(args.cards)

    turns = args.turns
    trials = args.trials
    cum_damage = []
    damage = []
    block = []
    best_attack = [0, None]
    worst_attack = [sys.maxsize, None]
    best_block = [0, None]
    worst_block = [sys.maxsize, None]
    for trial in range(trials):
        player = strategy(Deck(cards, seed=trial))
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
        if trial % 100 == 0:
            print(".", end='', file=sys.stderr, flush=True)
    print("", file=sys.stderr)
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
