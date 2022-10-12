from card import Card
import logging

logger = logging.getLogger("turns").getChild(__name__)


class CsvLogger():
    def __init__(self, logger=logging.getLogger("csv").info):
        self._plays = []
        self._turns = []
        self._game = 0
        self._logger = logger
        self._header_printed = False

    def end_game(self, final_hp):
        if self._plays:
            self.next_turn()
        if not self._header_printed:
            self._logger(
                "FINAL_HP,GAME,N_TURN,N_PLAY,ENERGY,PLAY,ATTACK,VULNERABLE,DEFEND,PLAYER_HP,MONSTER_HP,MONSTER_ATTACK,MONSTER_BLOCK")
            self._header_printed = True
        for n_turn, turn in enumerate(self._turns):
            for n_play, play in enumerate(turn):
                c_attrs = 0, 0, 0

                energy, card, player_hp, monster_hp, monster_attack, monster_block = play
                if card == Card.STRIKE:
                    c_attrs = 6, 0, 0
                elif card == Card.BASH:
                    c_attrs = 8, 2, 0
                elif card == Card.DEFEND:
                    c_attrs = 0, 0, 5
                self._logger("%d,%d,%d,%d,%d,%s,%d,%d,%d,%d,%d,%d,%d",
                             final_hp, self._game, n_turn, n_play,
                             energy, card.name, *c_attrs,
                             player_hp, monster_hp, monster_attack, monster_block)
        self._plays = []
        self._turns = []

        self._game += 1

    def play_card(self, energy: int, c: Card, player_hp: int,
                  monster_hp: int, monster_attack: int, monster_block: int):
        self._plays.append(
            (energy, c, player_hp, monster_hp, monster_attack, monster_block))

    def next_turn(self):
        self._turns.append(self._plays)
        self._plays = []
