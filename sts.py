import math
import logging
import numpy
import matplotlib.pyplot as plt
from enum import Enum
from collections import namedtuple

class CardArgs(namedtuple('CardArgs',
              'energy attack exhaustible strength_gain vulnerable')):
    def __new__(cls, energy, 
                attack=0,
                exhaustible=False,
                strength_gain=0,
                vulnerable=0):
        return super().__new__(cls, energy, 
                                attack,
                                exhaustible,
                                strength_gain,
                                vulnerable)
    def __getnewargs__(self):
        return (self.energy, 
                self.attack,
                self.exhaustible,
                self.strength_gain,
                self.vulnerable)

class Card(CardArgs, Enum):
  BASH = CardArgs(2, attack=8, vulnerable=2)
  DEFEND = CardArgs(1)
  DEMON_FORM = CardArgs(3, exhaustible=True, strength_gain=2)
  STRIKE = CardArgs(1, attack=6)

IRONCLAD_STARTER = [Card.DEFEND]*4 + [Card.STRIKE]*5 + [Card.BASH]
class Deck:
  def __init__(self, cards, seed=1):
    self.deck = cards.copy()
    self.discards = []
    numpy.random.seed(seed=seed)
    numpy.random.shuffle(self.deck)

  def deal(self):
    if not self.deck:
      if self.discards:
        self.deck = self.discards
        logging.info("shuffling...")
        numpy.random.shuffle(self.deck)
        self.discards = []

    if self.deck:
      return self.deck.pop(0)

    return None

  def deal_multi(self, count):
    ret = []
    while count > 0:
      card = self.deal()
      if not card:
        return ret
      count -= 1
      ret.append(card)
    return ret

  def discard(self, cards):
    self.discards.extend(cards)

class Monster:
  def __init__(self) -> None:
    self._damage = []
    self._turn = 0
    self._vulnerable = 0

  def begin_turn(self):
    self._damage.append(0)
  
  def defend(self, attack):
    self._damage[self._turn] += attack * (1.5 if self._vulnerable else 1.0)
    logging.debug(f"{self._turn}: MONSTER TAKING DAMAGE: vuln: {self._vulnerable}: {attack} -> {self._damage[self._turn]}")

  def vulnerable(self, turns):
    self._vulnerable += turns
    logging.debug(f"{self._turn}: MONSTER TAKING VULNERABLE:{turns} -> {self._vulnerable}")

  def end_turn(self):
    if self._vulnerable > 0:
      self._vulnerable -= 1
    self._turn += 1
    
  def get_damage(self):
    return self._damage

class Player:
  def __init__(self, deck: Deck) -> None:
    self.deck = deck
    self.strength = 0

  def play_turn(self, monster: Monster):
    monster.begin_turn()

    hand = self.deck.deal_multi(5)
    # print(f"HAND: {hand}")
    hand.sort(reverse=True, key=lambda c: c.energy)
    energy = 3
    for card in hand:
      if energy < card.energy:
        break

      if card.attack or card.strength_gain:
        logging.info(f"playing card: {card}")
        energy -= card.energy

        if card.attack:
          monster.defend(card.attack + self.strength)
      
        if card.vulnerable:
          monster.vulnerable(card.vulnerable)

        if card.strength_gain:
          self.strength += card.strength_gain

        if card.exhaustible:
          hand.remove(card)

    
    self.deck.discard(hand)    

    monster.end_turn()

  def play_game(self, monster: Monster, turns: int):
    for turn in range(turns):
      self.play_turn(monster)

def get_frontloaded_damage(damage: list):
  return (damage[0] + 
          damage[1]/2.0 + 
          damage[2]/4.0 + 
          damage[3]/8.0)

def get_scaling_damage(damage: list):
  return (damage[10] - damage[1]) / 10.0

def create_scatter_plot_data(plot_data):
  trials = len(plot_data)
  plot_data = numpy.swapaxes(plot_data, 0, 1)
  scatter_data = {}
  scatter_data['turns'] = []
  scatter_data['damage'] = []
  size = []
  logging.debug(f"plot_data: {plot_data}")
  for turn in range(len(plot_data)):
    turn_damage = plot_data[turn]
    r = range(int(min(turn_damage)), 2+int(max(turn_damage)))
    hist = numpy.histogram(turn_damage, bins=r)
    for bin_count, bin in zip(*hist):
      if bin_count:
        scatter_data['turns'].append(turn)
        scatter_data['damage'].append(bin)
        size.append(bin_count/(trials/100.0))
    if turn == 0:
      logging.debug(f"TURN0 hist: {hist}")
      logging.debug(f"TURN0 size: {size}")
      logging.debug(f"TURN0 scatter_data {scatter_data}")
 
  return scatter_data, size

def main():
  turns = 16
  trials = 1000
  cum_damage = []
  damage = []
  for trial in range(trials):
    player = Player(Deck(IRONCLAD_STARTER, seed=trial))
    monster = Monster()
    player.play_game(monster, turns)
    damage.append(monster.get_damage())
    cum_damage.append(numpy.cumsum(monster.get_damage()))

  logging.debug(f"damage: {damage}")
  scatter_data, size = create_scatter_plot_data(damage)
 
  average_damage = numpy.average(damage, axis=0)
  logging.debug(f"scatter_data: {scatter_data}, {size}")
  print(f"average: {average_damage}")
  print(f"FRONTLOADED DAMAGE {get_frontloaded_damage(average_damage):.2f}")
  print(f"SCALING DAMAGE {get_scaling_damage(average_damage):.2f}")
  fig, ax = plt.subplots()
  ax.scatter('turns', 'damage', s=size, data = scatter_data)

  plt.show()

if __name__ == "__main__":
    main()
