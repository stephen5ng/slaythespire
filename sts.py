import math
import logging
import numpy
import matplotlib.pyplot as plt
from enum import Enum
from collections import namedtuple
import numpy.polynomial.polynomial as poly

logging.basicConfig(filename='sts.log', encoding='utf-8', level=logging.INFO)

class CardArgs(namedtuple('CardArgs',
              'energy attack attack_multiplier exhaustible strength_gain strength_gain_buff strength_multiplier vulnerable')):
    def __new__(cls, energy, 
                attack=0,
                attack_multiplier=1,
                exhaustible=False,
                strength_gain=0,
                strength_gain_buff=0,
                strength_multiplier=1,
                vulnerable=0):
        return super().__new__(cls, energy, 
                                attack,
                                attack_multiplier,
                                exhaustible,
                                strength_gain,
                                strength_gain_buff,
                                strength_multiplier,
                                vulnerable)
    def __getnewargs__(self):
        return (self.energy, 
                self.attack,
                self.attack_multiplier,
                self.exhaustible,
                self.strength_gain,
                self.strength_gain_buff,
                self.strength_multiplier,
                self.vulnerable)

class Card(CardArgs, Enum):
  ANGER = CardArgs(0, attack=6)
  BASH = CardArgs(2, attack=8, vulnerable=2)
  DEFEND = CardArgs(1)
  DEMON_FORM = CardArgs(3, exhaustible=True, strength_gain_buff=2)
  HEAVY_BLADE = CardArgs(1, attack=14, strength_multiplier=3)
  INFLAME = CardArgs(1, exhaustible=True, strength_gain=2)
  STRIKE = CardArgs(1, attack=6)
  TWIN_STRIKE = CardArgs(1, attack=5, attack_multiplier=2)
  def __str__(self):
    return self.name

  def __repr__(self):
    return self.name

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
    self.strength_gain_buff = 0

  def _play_hand(self, hand: list, monster: Monster):
    hand.sort(reverse=True, key=lambda c: (c.energy, c.exhaustible))

    logging.debug(f"HAND: {hand}")

    energy = 3
    played_cards = []
    for card in hand:
      if card.energy and energy < card.energy:
        continue

      if card.attack or card.strength_gain or card.strength_gain_buff:
        logging.debug(f"playing card: {card}")
        played_cards.append(card)
        energy -= card.energy

        if card.attack:
          monster.defend(card.attack_multiplier * 
                        (card.attack + self.strength * card.strength_multiplier))
      
        if card.vulnerable:
          monster.vulnerable(card.vulnerable)

        if card.strength_gain_buff:
          self.strength_gain_buff += card.strength_gain_buff

        if card.strength_gain:
          self.strength += card.strength_gain

        if card.exhaustible:
          hand.remove(card)

    return played_cards

  def play_turn(self, monster: Monster):
    monster.begin_turn()
    self.strength += self.strength_gain_buff        
    hand = self.deck.deal_multi(5)

    played_cards = self._play_hand(hand, monster)
    logging.info(f"Played: {played_cards}")

    self.deck.discard(hand)    
    monster.end_turn()

  def play_game(self, monster: Monster, turns: int):
    for turn in range(turns):
      self.play_turn(monster)
    # logging.info(f"damage: {numpy.cumsum(monster.get_damage())}")

    logging.info(f"damage: {monster.get_damage()}")

def get_frontloaded_damage(damage: list):
  return (damage[0] + 
          damage[1]/2.0 + 
          damage[2]/4.0 + 
          damage[3]/8.0)

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
  turns = 40
  trials = 1000
  cum_damage = []
  damage = []
  cards = [Card.DEFEND]*4 + [Card.STRIKE]*4 + [Card.HEAVY_BLADE] + [Card.BASH] + [Card.DEMON_FORM]
  for trial in range(trials):
    player = Player(Deck(cards, seed=trial))
    monster = Monster()
    player.play_game(monster, turns)
    damage.append(monster.get_damage())
    cum_damage.append(numpy.cumsum(monster.get_damage()))

  logging.debug(f"damage: {damage}")
  scatter_data, size = create_scatter_plot_data(damage)
 
  average_damage = numpy.average(damage, axis=0)
  turns_after_first_deck = 2+int(len(cards) / 5)
  x = list(range(turns))
  x_after_first_deck = x[turns_after_first_deck:]
  coefs = poly.polyfit(x_after_first_deck, average_damage[turns_after_first_deck:], 3)
  ffit = poly.polyval(x_after_first_deck, coefs)

  logging.debug(f"scatter_data: {scatter_data}, {size}")
  print(f"average: {average_damage}")
  print(f"FRONTLOADED DAMAGE {get_frontloaded_damage(average_damage):.2f}")
  print(f"SCALING DAMAGE: " + str([f"{cc:.1f}" for cc in coefs[1:]]))
  fig, ax = plt.subplots()
  plt.plot(x_after_first_deck, ffit, color='green')

  ax.scatter(x, average_damage, s=4, color='red', marker="_")

  ax.scatter('turns', 'damage', s=size, data=scatter_data)

  plt.show()

if __name__ == "__main__":
    main()
