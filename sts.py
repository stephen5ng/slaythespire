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

def play_turn(deck):
    vulnerable = 0
    hand = deck.deal_multi(5)
    damage = 0
    hand.sort(reverse=True, key=lambda c: c.energy)
    energy = 3
    for card in hand:
      if energy < card.energy:
        break
      if card.attack:
        damage += card.attack * (1.5 if vulnerable else 1.0)
        energy -= card.energy
      
      if card.vulnerable:
        vulnerable += 1
      
    deck.discard(hand)
    print(f"damage: {damage}")
    vulnerable -= 1
    return damage

def play_game(deck, turns):
  damage = []
  cum_damage = 0
  for turn in range(turns):
    cum_damage += play_turn(deck)
    damage.append(cum_damage)
  return damage

def main():
  cards = [Card.DEFEND]*5 + [Card.STRIKE]*5
  deck = Deck(cards)
  turns = 20
  trials = 100
  data = []
  turn_0 = []
  for trial in range(trials):
    damage = play_game(deck, turns)
    data.append(damage)

  data = numpy.swapaxes(data, 0, 1)
  scatter_data = {}
  scatter_data['turns'] = []
  scatter_data['damage'] = []
  size = []
  print(f"data: {data}")
  for turn in range(turns):
    damage = data[turn]
    hist = numpy.histogram(damage, bins=max(damage)-min(damage))
    for h0, h1 in zip(*hist):
      scatter_data['turns'].append(turn)
      scatter_data['damage'].append(h1)
      size.append(h0)
 
  print(f"hist: {data}, {scatter_data}, {size}")
  fig, ax = plt.subplots()
  ax.scatter('turns', 'damage', s=size, data = scatter_data)

  # print(f"attack: {data}")
  # fig, ax = plt.subplots()
  # ax.scatter('turns', 'damage', c='color', s=2.0, data = data)
  # ax.set_xlabel('turn')
  # ax.set_ylabel('damage')
  
  plt.show()

if __name__ == "__main__":
    main()

class Monster:
  def __init__(self):
    self.hp = 100
  
  def defend(self, attack):
    self.hp -= attack

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
