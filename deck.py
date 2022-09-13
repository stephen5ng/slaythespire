import logging
import logging.config
from logging import config
from typing import List, Union

import numpy

from card import Card

logger = logging.getLogger("turns").getChild(__name__)

class Deck:
    def __init__(self, cards, seed=1, shuffle=True):
        self._deck = cards.copy()
        self._discards = []
        self._hand = []
        self._exhausted = []
        self._deals = 0
        numpy.random.seed(seed=seed)
        if shuffle:
            numpy.random.shuffle(self._deck)
        logger.info(f"Deck: {self._deck}")

    def _deal(self) -> Union[Card, None]:
        logger.debug(f"_deal: {self}")

        if not self._deck:
            if self._discards:
                self._deck = self._discards.copy()
                self._discards = []
                logger.info(f"shuffling...")
                numpy.random.shuffle(self._deck)
                logger.debug(f"{self}")

        if not self._deck:
            return None
        dealt = self._deck.pop(0)
        self._hand.append(dealt)
        return dealt

    def deal(self, count=1) -> List[Card]:
        logger.debug(f"deal: {self}")
        cards = []
        while count > 0:
            card = self._deal()
            if not card:
                return cards
            count -= 1
            cards.append(card)

        logger.debug(f"deals: {self._deals}, dealt {self}")
        logger.info(f"hand {self.hand}")

        self._deals += 1 # 
        return cards

    def add_to_discards(self, cards):
        logger.debug(f"add_to_discard {cards} for {self}")
        self._discards.extend(cards)

    def discard_from_hand(self, cards):
        logger.debug(f"discarding {cards} from {self}")
        for card in cards:
            self._hand.remove(card)

        self.add_to_discards(cards)
            
    def exhaust(self, cards):
        for card in cards:
            self._hand.remove(card)
        self._exhausted.extend(cards)

    def all_cards(self) -> List[Card]:
        # Does not include exhaust
        return self._hand + self._deck + self._discards

    def sort_hand(self, key):
        self._hand.sort(reverse=True, key=key)
        logger.debug(f"SORTED {self._hand}")

    def __str__(self):
        return f"hand: {self._hand}, discards: {self._discards}, exhausted: {self.exhausted}, deck: {self._deck}"

    def get_deck(self):
        return self._deck.copy()

    def get_discards(self):
        return self._discards.copy()

    def get_exhausted(self):
        return self._exhausted.copy()

    def get_hand(self):
        return self._hand.copy()

    deck = property(get_deck)
    discards = property(get_discards)
    exhausted = property(get_exhausted)
    hand = property(get_hand)
