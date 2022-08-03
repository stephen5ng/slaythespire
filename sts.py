import math
from re import M
import numpy
import matplotlib.pyplot as plt
from enum import Enum
from collections import namedtuple

class CardArgs(namedtuple('CardArgs', "energy attack_damage")):
    def __new__(cls, energy, attack_damage=0):
        return super().__new__(cls, energy, attack_damage)
    def __getnewargs__(self):
        return (self.energy, self.attack_damage)

class Card(CardArgs, Enum):
  STRIKE = CardArgs(1, attack_damage=6)
  DEFEND = CardArgs(1)

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
    hand = deck.deal_multi(5)
    damage = 0
    played_cards = []
    for card in hand:
      if card.attack_damage:
        damage += card.attack_damage
        played_cards.append(card)
        if len(played_cards) >= 3:
          break
    deck.discard(hand)
    print(f"damage: {damage}")
    return damage

def play_game(deck, turns):
  damage = []
  cum_damage = 0
  for turn in range(turns):
    cum_damage += play_turn(deck)
    damage.append(cum_damage)
  return damage

def main():
  cards = [DEFEND]*5 + [STRIKE]*5
  deck = Deck(cards)
  data = {}
  turns = 20
  for trial in range(10):
    damage = play_game(deck, turns)
    data['turns'] = data.get('turns', []) + list(range(turns))
    data['damage'] = data.get('damage', []) + damage.copy()
    data['color'] = data.get('color', []) + [1+trial*3]*turns
  
  print(f"attack_damage: {data}")
  fig, ax = plt.subplots()
  ax.scatter('turns', 'damage', c='color', s=2.0, data = data)
  ax.set_xlabel('turn')
  ax.set_ylabel('damage')
  
  plt.show()

if __name__ == "__main__":
    main()

class Monster:
  def __init__(self):
    self.hp = 100
  
  def defend(self, attack_damage):
    self.hp -= attack_damage

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
