"""This file compares the profit distribution and mev rate of PoS with and without PBS"""

import random
import numpy as np

random.seed(42)

NUM_USERS = 100
NUM_BUILDERS = 20
NUM_VALIDATORS = 20
NUM_PROPOSERS = 5 
BLOCK_CAPACITY = 50
NUM_TRANSACTIONS = 100

class Transaction:
    def __init__(self, fee, is_mev, creator_id=None):
        self.fee = fee
        self.is_mev = is_mev
        self.creator_id = creator_id

class Participant:
    def __init__(self, id, is_mev_oriented):
        self.id = id
        self.is_mev_oriented = is_mev_oriented

    
class Builder(Participant):
    pass

class Validator(Participant):
    pass

class run_PBS:
    pass

class run_PoS:
    pass
