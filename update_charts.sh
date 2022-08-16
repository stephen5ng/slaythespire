#!/bin/bash

python3 sts.py "IRONCLAD_STARTER" --strategy=AttackingPlayer --trials=10000 --turns=60 --write
python3 sts.py "IRONCLAD_STARTER + [Card.DEMON_FORM]" --strategy=AttackingPlayer --trials=10000 --turns=60 --write
python3 sts.py "IRONCLAD_STARTER + [Card.LIMIT_BREAK_PLUS] + [Card.FLEX]" --trials=1000 --turns=40 --write
python3 sts.py "IRONCLAD_STARTER" --strategy=AttackingPlayer --trials=1000 --turns=20 --monster=JawWorm --write 

