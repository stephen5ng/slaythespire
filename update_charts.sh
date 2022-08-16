#!/bin/bash

python3 sts.py "[Card.DEFEND]*4 + [Card.STRIKE]*5 + [Card.BASH]" --strategy=AttackingPlayer --trials=10000 --turns=60
python3 sts.py "[Card.DEFEND]*4 + [Card.STRIKE]*5 + [Card.BASH] + [Card.DEMON_FORM]" --strategy=AttackingPlayer --trials=10000 --turns=60
python3 sts.py "[Card.DEFEND]*4 + [Card.STRIKE]*4 + [Card.BASH] + [Card.LIMIT_BREAK_PLUS] + [Card.FLEX]" --trials=1000 --turns=40
python3 sts.py "[Card.DEFEND]*4 + [Card.STRIKE]*5 + [Card.BASH]" --strategy=AttackingPlayer --trials=1000 --turns=20 --monster=JawWorm   