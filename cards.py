import math
import numpy

class Card:
  def __init__(self, attack):
    self.attack = attack

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
