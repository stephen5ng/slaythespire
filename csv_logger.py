from card import Card
import logging
from typing import Sequence

logger = logging.getLogger("turns").getChild(__name__)


class CsvLogger():
    def __init__(self, header: str, logger=logging.getLogger("csv").info):
        self._plays = []
        self._turns = []
        self._game = 0
        self._logger = logger
        self._header = header
        self._header_printed = False

    def end_game(self, final_hp):
        if self._plays:
            self.next_turn()
        if not self._header_printed:
            self._logger(self._header)
            self._header_printed = True
        for n_turn, turn in enumerate(self._turns):
            for n_play, play in enumerate(turn):
                self._logger("%s", str((final_hp, self._game, n_turn, n_play) + play)[1:-1]
                             .replace("'", "")
                             .replace(" ", ""))
        self._plays = []
        self._turns = []

        self._game += 1

    def play_card(self, elements: Sequence):
        self._plays.append(elements)

    def next_turn(self):
        self._turns.append(self._plays)
        self._plays = []
       