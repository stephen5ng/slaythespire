
CARDS = ["STRIKE", "BASH", "DEFEND"]
CONT_DATA = ("ENERGY,"
             "PLAYER_HP,PLAYER_BLOCK,"
             "MONSTER_HP,MONSTER_ATTACK,MONSTER_BLOCK,MONSTER_VULNERABLE," +
             ",".join([f"HAND_{c}" for c in CARDS]))
