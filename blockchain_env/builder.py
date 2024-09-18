import random

BLOCK_CAP = 100

class Builder:
    def __init__(self, builder_id, is_attacker, balance):
        self.id = builder_id
        self.is_attacker = is_attacker
        self.balance = balance
        self.mempool = []

    def launch_attack(self, block_num):
        # this is for the attack builder, after identifying the target transaction, they will launch attack with 0 gas fee and 0 mev potential, they include this attack directly in the block that they are building
        mev_potential = 0
        gas_fee = 0

        attack_type = random.choice(['front', 'back', 'sandwich'])


    def select_transactions(self):
        # select transactions from the mempool
        # if is attacker, select transactions with highest mev_potential + gas fee
        # if not attacker, select transactions with highest gas fee
        # return the selected transactions
        if self.is_attacker == True:
            self.mempool.sort(key=lambda x: x['mev_potential'] + x['gas_fee'], reverse=True)
        else:
            self.mempool.sort(key=lambda x: x['gas_fee'], reverse=True)
        return self.mempool[:10]
        
        # for the non-attacker builder, just select the trasnctions based on gas fee untill block limit is reached
        # for the attacker, if a trasnctions has mev potential: to get the profit, they need to attack it.

    def bid(self, transaction):