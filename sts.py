import argparse
import logging
import logging.config
import math
import sys
from collections import namedtuple
from telnetlib import SE
from typing import Sequence

import numpy
import numpy.polynomial.polynomial as poly
import numpy.typing
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from card import IRONCLAD_STARTER, Card
from deck import Deck
from monster import JawWorm, Monster
from player import AttackingPlayer, DefendingPlayer

logging.config.fileConfig(fname='logging.conf', disable_existing_loggers=False)
turn_logger = logging.getLogger("turns")
logger = logging.getLogger("sts")

MAX_BUBBLE_SIZE = 20
MIN_BUBBLE_SIZE = 1


def get_frontloaded_damage(damage: list, scale=True):
    fld = 0.0
    scaling = 1.0
    for ix in range(min(len(damage), 4)):
        fld += damage[ix] * (scaling if scale else 1.0)
        scaling /= 2.0
    print(f"FRONTLOADED DAMAGE: {fld:.2f}")
    return fld


def histogram(values_by_trial: numpy.typing.NDArray):
    values_by_turn = numpy.swapaxes(values_by_trial, 0, 1)
    logger.debug(f"histogram values_by_turn {values_by_turn}")
    hists = []
    for turn in range(len(values_by_turn)):
        values = values_by_turn[turn]
        values = values[values != -1.0]
        r = range(int(min(values)), 2+int(max(values)))
        hist = numpy.histogram(values, bins=r)
        hists.append(hist)

    logger.debug(f"histogram --> {hists}")
    return hists


def create_scatter_plot_data(values_by_trial):
    # plot_data is an array of trials, where each trial is an array of values (e.g. damage or block).
    # returns scatter plot data based on a histogram of the trial data.
    # create_scatter_plot_data returns:
    # - scatter_data: a dictionary with two values:
    #     - turns: array of turn numbers (one per data point)
    #     - value: array of values (one per histogram bin)
    # - size: array of sizes (one per data point); sizes are proportional to histogram bucket counts
    # - sizes_by_value_by_turn: array (one per turn) of dictionary of sizes with the value as the key
    logger.debug(
        f"create_scatter_plot_data values_by_trial: {values_by_trial}")

    trials = len(values_by_trial)
    values_by_turn = numpy.swapaxes(values_by_trial, 0, 1)
    scatter_data = {}
    scatter_data['turns'] = []
    scatter_data['value'] = []
    size = []
    sizes_by_value_by_turn = []
    histograms = histogram(values_by_trial)
    for turn in range(len(values_by_turn)):
        sizes_by_value = {}
        hist = histograms[turn]
        for bin_count, bin in zip(*hist):
            if bin_count:
                scatter_data['turns'].append(turn)
                scatter_data['value'].append(bin)
                s = bin_count/(trials/100.0)
                sizes_by_value[bin] = s
                size.append(s)
        sizes_by_value_by_turn.append(sizes_by_value)
        logger.debug(f"TURN {turn} scatter_data {scatter_data}")
        logger.debug(f"TURN {turn} size: {size}")
        logger.debug(
            f"TURN {turn} sizes_by_value_by_turn {sizes_by_value_by_turn}")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"TURN hist: {hist}")
            logger.debug(f"TURN size: {size}")
            logger.debug(f"TURN scatter_data {scatter_data}")

    logger.debug(
        f"scatter_data: {scatter_data}, {size}, {sizes_by_value_by_turn}")

    return scatter_data, size, sizes_by_value_by_turn


def format_scaling_damage(coefs: Sequence):
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


def plot_one_attribute(data, size_by_turn, color, name, marker: dict):
    marker = marker.copy()
    marker['size'] = []
    marker['color'] = color
    for i in range(len(data)):
        marker['size'].append(size_by_turn[i][data[i]])

    return go.Scatter(x=list(range(len(data))), y=data, mode='markers', marker=marker, name=name)


def pad_to_dense(M):
    """Appends the minimal required amount of -1's at the end of each
     array in the jagged array `M`, such that `M` loses its jagedness."""

    if len(M) == 0:
        return numpy.array([])

    maxlen = max(len(r) for r in M)

    Z = numpy.zeros((len(M), maxlen))
    Z -= 1
    for enu, row in enumerate(M):
        Z[enu, :len(row)] += 1
        Z[enu, :len(row)] += row
    return Z


class TrialStats:
    def __init__(self):

        # TODO(sng): convert to numpy arrays
        self.monster_damage = []
        self.cum_monster_damage = []
        self.player_block = []
        self.turns = []
        self.player_final_hp = []

    def add_player_block(self, block):
        self.player_block.append(block)
        self.turns.append(len(block))

    def add_monster_damage(self, damage: Sequence):
        self.monster_damage.append(damage)

    def add_player_hp(self, hp):
        self.player_final_hp += [hp]

    def _average(self, padded: numpy.typing.NDArray):
        average = []
        if padded.size:
            value_by_turn = numpy.swapaxes(padded, 0, 1)
            for trial in value_by_turn:
                average += [numpy.average(trial[trial != -1])]
        return average

    def finish(self):
        self.monster_damage_dense = pad_to_dense(self.monster_damage)
        self.player_block_dense = pad_to_dense(self.player_block)

        self.average_monster_damage = self._average(self.monster_damage_dense)
        self.cum_monster_damage = numpy.sum(self.average_monster_damage)

        self.average_player_block = self._average(self.player_block_dense)

        logger.debug(f"trial_stats damage: {self.monster_damage}")
        logger.debug(f"trial_stats block: {self.player_block}")
        logger.debug(f"trial_stats turns: {self.turns}")
        logger.debug(f"trial_stats player_final_hp: {self.player_final_hp}")
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


def get_damage_stats(deck_size: int, trial_stats: TrialStats):
    # Calculate big-O stats after going through the deck a couple times.
    turns_after_first_deck = 2 * int(deck_size / 5)
    if len(trial_stats.average_monster_damage) - turns_after_first_deck < 2:
        turns_after_first_deck = 0
    x = list(range(len(trial_stats.average_monster_damage)))
    x_after_first_deck = x[turns_after_first_deck:]

    coefs, residuals, ffit = curve_fit(
        x_after_first_deck, trial_stats.average_monster_damage[turns_after_first_deck:])

    scaled_residuals = residuals/len(x_after_first_deck)
    logger.debug(f"scaled residuals: {scaled_residuals}")
    scaling = format_scaling_damage(coefs)
    if abs(scaled_residuals) > 10000:
        # Error too large, try exponential function.
        log_average_monster_damage = [
            math.log(d, 2) for d in trial_stats.average_monster_damage]

        coefs, residuals_log, log_ffit = curve_fit(
            x_after_first_deck, log_average_monster_damage[turns_after_first_deck:])
        logger.debug(f"residuals: {residuals}, {residuals_log}")
        ffit = [math.pow(2, y) for y in log_ffit]
        scaling = f"O({coefs[1]:.2f}*2^n)"

    print(f"SCALING DAMAGE: coefs: {coefs}, {scaling}")

    return scaling, x_after_first_deck, ffit


def plot_attack_damage(trial_stats: TrialStats, combat_log: CombatLog, card_size):
    scaling_damage, fit_x, fit_y = get_damage_stats(card_size, trial_stats)

    damage_scatter_data, size, sizes_by_damage_by_turn = create_scatter_plot_data(
        trial_stats.monster_damage_dense)

    logger.debug(
        f"best damage {combat_log.best_attack.Damages}, {size}, {sizes_by_damage_by_turn}")
    damage_marker = dict(
        size=size,
        sizemode='area',
        sizeref=2.*max(size)/(MAX_BUBBLE_SIZE**2),
        sizemin=MIN_BUBBLE_SIZE)
    best = plot_one_attribute(combat_log.best_attack.Damages,
                              sizes_by_damage_by_turn, 'lime', 'best', damage_marker)
    worst = plot_one_attribute(combat_log.worst_attack.Damages,
                               sizes_by_damage_by_turn, 'lightcoral', 'worst', damage_marker)

    traces = [go.Scatter(opacity=.5, x=damage_scatter_data['turns'], y=damage_scatter_data['value'], mode='markers',
                         marker=damage_marker,
                         name="damage"),
              go.Scatter(y=trial_stats.average_monster_damage, line=dict(color='grey', width=1,
                                                                         dash='dot'), name='average'),
              go.Scatter(x=fit_x, y=fit_y, line_color='grey', name='curve fit'), best, worst]

    block = plot_player_block(trial_stats)
    traces.extend(block[0])
    title = (f'ATTACK total: {trial_stats.cum_monster_damage:.2f} ({combat_log.worst_attack.TotalDamage} to {combat_log.best_attack.TotalDamage})' +
             f' frontload: {get_frontloaded_damage(trial_stats.average_monster_damage):.2f} hp scaling: {scaling_damage} | BLOCK {block[1]}')
    return traces, title


def plot_player_block(trial_stats: TrialStats):
    block_scatter_data, size, _ = create_scatter_plot_data(
        trial_stats.player_block_dense)
    traces = [
        go.Scatter(opacity=.5, x=block_scatter_data['turns'], y=block_scatter_data['value'], mode='markers',
                   marker=dict(
            symbol='star-square',
            color='turquoise',
            line_color='lightskyblue',
            size=size,
            sizemode='area',
            sizeref=2.*max(size)/(MAX_BUBBLE_SIZE**2),
            sizemin=MIN_BUBBLE_SIZE), name="block"),
        go.Scatter(opacity=.3, mode='lines', y=trial_stats.average_player_block, line=dict(color='turquoise', width=16,
                                                                                           dash='solid'), name='average')]

    title = f'avg: {numpy.average(trial_stats.average_player_block):.2f}'
    return traces, title


def plot_player_hp(trial_stats: TrialStats):
    return [go.Histogram(y=trial_stats.player_final_hp)], "player hp"


def main():
    logger.debug(f"starting...")
    logger.info(f"info starting...")

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
    argparser.add_argument(
        '--write', help='write chart to disk', action="store_true")
    args = argparser.parse_args()
    strategy = eval(args.strategy)
    cards = eval(args.cards)

    # Prevent pyflake from removing thise imports
    logger.debug(
        f"dynamic imports: {JawWorm}, {Monster}, {AttackingPlayer}, {DefendingPlayer}, {Card}, {IRONCLAD_STARTER}")
    monster_factory = eval(args.monster)

    trial_stats = TrialStats()
    combat_log = CombatLog()
    turns = args.turns
    trials = args.trials

    for trial in range(trials):
        player = strategy(Deck(cards, seed=trial))
        monster = monster_factory()
        player.play_game(monster, turns)
        trial_stats.add_monster_damage(monster.get_damage())
        trial_stats.add_player_block(player.blocks)
        trial_stats.add_player_hp(player.hp)
        total_damage = numpy.sum(monster.get_damage())
        combat_log.add_combat(total_damage, TurnInfo(
            total_damage, player.played_cards, monster.get_damage()))
        combat_log.add_block(numpy.sum(player.blocks), player.played_cards)
        if trial % 100 == 0:
            print(".", end='', file=sys.stderr, flush=True)
    print("", file=sys.stderr)
    combat_log.finish()
    trial_stats.finish()

    traces_and_titles = []

    traces_and_titles.append(plot_attack_damage(
        trial_stats, combat_log, len(cards)))

    if min(trial_stats.player_final_hp) != max(trial_stats.player_final_hp):
        traces_and_titles.append(plot_player_hp(trial_stats))

    title = "IRONCLAD BASE" if len(
        sys.argv) <= 1 else f'{args.strategy} vs {args.monster}<sup><br>{args.cards}</sup>'
    titles = [t[1] for t in traces_and_titles]

    fig = make_subplots(rows=1, cols=len(
        traces_and_titles), subplot_titles=titles)
    fig.update_layout(paper_bgcolor='ghostwhite', plot_bgcolor='ghostwhite')

    for i, trace_and_title in enumerate(traces_and_titles, 1):
        traces = trace_and_title[0]
        fig.add_traces(traces, cols=[i]*len(traces), rows=[1]*len(traces))

    fig.update_layout(title_text=title)
    fig.update_layout(title_font_size=18)
    fig.update_layout(title_x=0.5)
    fig.update_annotations(font_size=12)
    if args.write:
        filename = f"charts/{' '.join(sys.argv[1:]).replace('--write', '').strip()}.html"
        fig.write_html(filename)
    logger.debug(f"fig: {fig}")

    fig.show()


if __name__ == "__main__":
    main()
