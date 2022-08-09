import argparse
import logging
import math
import sys
from collections import namedtuple

import matplotlib.pyplot as plt
import numpy
import numpy.polynomial.polynomial as poly

from card import Card
from deck import Deck
from monster import JawWorm, Monster
# from player import AttackingPlayer, DefendingPlayer

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)


def main():
    logging.basicConfig(filename='sts.log',
                        encoding='utf-8', level=logging.DEBUG)

    logging.debug(f"starting...")
    logging.info(f"info starting...")


if __name__ == "__main__":
    main()
logging.debug("hello")
