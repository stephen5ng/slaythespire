import math
from re import M
import numpy
import matplotlib.pyplot as plt
from enum import Enum
from collections import namedtuple

class CardArgs(namedtuple('CardArgs', "energy attack vulnerable")):
    def __new__(cls, energy, 
                attack=0,
                vulnerable=0):
        return super().__new__(cls, energy, 
                                attack,
                                vulnerable)
    def __getnewargs__(self):
        return (self.energy, 
                self.attack,
                self.vulnerable)

class Card(CardArgs, Enum):
  BASH = CardArgs(2, attack=8, vulnerable=2)
  DEFEND = CardArgs(1)
  STRIKE = CardArgs(1, attack=6)

class Deck:
  def __init__(self, cards, seed=1):
    self.deck = cards
    self.discards = []
    numpy.random.seed(seed=seed)
    numpy.random.shuffle(self.deck)

  def deal(self):
    if not self.deck:
      if self.discards:
        self.deck = self.discards
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

  def __str__(self):
    return "\n".join([c.name for c in self.cards])

class Monster:
  def __init__(self) -> None:
    self._damage = []
    self._turn = 0
    self._vulnerable = 0

  def begin_turn(self):
    self._damage.append(0)
  
  def defend(self, attack):
    self._damage[self._turn] += attack * (1.5 if self._vulnerable else 1.0)
    # print(f"{self._turn}: MONSTER TAKING DAMAGE: {self._vulnerable}: {attack} -> {self._damage[self._turn]}")
  
  def vulnerable(self, turns):
    self._vulnerable += turns
    # print(f"{self._turn}: MONSTER TAKING VULNERABLE:{turns} -> {self._vulnerable}")

  def end_turn(self):
    if self._vulnerable > 0:
      self._vulnerable -= 1
    self._turn += 1
    
  def get_damage(self):
    return self._damage

def play_turn(deck, monster):
    monster.begin_turn()
    hand = deck.deal_multi(5)
    # print(f"HAND: {hand}")
    hand.sort(reverse=True, key=lambda c: c.energy)
    energy = 3
    for card in hand:
      if energy < card.energy:
        break
      if card.attack:
        monster.defend(card.attack)
        energy -= card.energy
      
      if card.vulnerable:
        monster.vulnerable(card.vulnerable)
    
    monster.end_turn()
    deck.discard(hand)

def play_game(deck, monster, turns):
  for turn in range(turns):
    play_turn(deck, monster)

def get_frontloaded_damage(damage):
  return (damage[0] + 
          damage[1]/2.0 + 
          damage[2]/4.0 + 
          damage[3]/8.0)

def main():
  cards = [Card.DEFEND]*4 + [Card.STRIKE]*5 + [Card.BASH]
  deck = Deck(cards)
  turns = 10
  trials = 1000
  cum_damage = []
  damage = []
  for trial in range(trials):
    monster = Monster()
    play_game(deck, monster, turns)
    damage.append(monster.get_damage())
    cum_damage.append(numpy.cumsum(monster.get_damage()))
  plot_data = damage
  print(f"damage: {damage}")

  plot_data = numpy.swapaxes(plot_data, 0, 1)
  scatter_data = {}
  scatter_data['turns'] = []
  scatter_data['damage'] = []
  size = []
  print(f"plot_data: {plot_data}")
  for turn in range(turns):
    turn_damage = plot_data[turn]
    r = range(int(min(turn_damage)), 2+int(max(turn_damage)))
    # print(f"turn {turn} damage: {turn_damage} r: {r}")
    hist = numpy.histogram(turn_damage, bins=r)
    for bin_count, bin in zip(*hist):
      if bin_count:
        scatter_data['turns'].append(turn)
        scatter_data['damage'].append(bin)
        size.append(bin_count/(trials/100.0))
    if turn == 0:
      print(f"TURN0 HIST: {hist}")
      print(f"TURN0 size: {size}")
      print(f"turn 0: {scatter_data}")
 
  average_damage = numpy.average(damage, axis=0)
  print(f"scatter_data: {scatter_data}, {size}")
  print(f"average: {average_damage}")
  print(f"FRONTLOADED DAMAGE {get_frontloaded_damage(average_damage):.2f}")
  fig, ax = plt.subplots()
  ax.scatter('turns', 'damage', s=size, data = scatter_data)

  plt.show()

if __name__ == "__main__":
    main()

class Player:
  def __init__(self, deck) -> None:
    self.deck = deck
    self.hand = deck.deal_multi(5)

  def play(self):
    for card in self.hand[:3]:
      card.play()
    

class Hand:
  def __init__(self, cards, dexterity, strength):
    self.cards = [card.name for card in cards]
    self.total_block = sum([card.get_block(dexterity) for card in cards])
    self.total_attack = sum([card.get_attack(strength) for card in cards])
    self.total_energy = sum([card.energy for card in cards])

  def __str__(self):
    return "%s => BLOCK: %d, ATTACK: %d" % (
        ", ".join(self.cards), self.total_block, self.total_attack)
    
class Hands:
  def __init__(self, deck, hand_size=5, dexterity=0, strength=0):
    self.deck = deck
    self.hand_size = hand_size
    self.dexterity = dexterity
    self.strength = strength
    self.hands = self.get_combinations()
    self.block_distribution = [h.total_block for h in self.hands]
    self.attack_distribution = [h.total_attack for h in self.hands]
    self.energy_distribution = [h.total_energy for h in self.hands]
