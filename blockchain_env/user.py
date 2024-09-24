import random

from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS
from blockchain_env.transaction import Transaction

random.seed(16)

BLOCKNUM = 50

# remember 1 initialise builders then users

class User:
    def __init__(self, user_id, is_attacker, builders):
        self.id = user_id
        self.is_attacker = is_attacker
        self.visible_builders = random.sample(builders, int(0.8 * len(builders)))

    def create_transactions(self, block_num):
        # create normal trasnctions with random gas fee and mev potential from the sample list
        gas_fee = random.choice(SAMPLE_GAS_FEES)
        mev_potential = random.choice(MEV_POTENTIALS)
        creator_id = self.id
        created_at = block_num
        target_tx = None
        return Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        
    def launch_attack(self, block_num):
        # if there are profitable transctions in the mempool, user can launch attack
        # the attack could be front, back, or sandwich attack (let this be random)
        # attack the transaction with highest mev potential (if you see that there are already a lot transactions taregting the same transaction, try to attack another one)
        # other attack transactions could be spotted by seeing that gas fee is similar to the target transaction
        # the more they see others attacking the same transaction, the more likely they are to attack the same transaction
        # if no transactions are with non zero mev potential, just create benign transactions
        
        # users can see the mempool of the visible builders
        # there are overlaps in builders' mempools, avoid double counting
        mempool_content = []
        for builder in self.visible_builders:
            if Transaction in builder.get_mempool() and Transaction not in mempool_content:
                mempool_content.append(Transaction)


        profitable_txs = [tx for tx in mempool_content if tx['mev_potential'] > 0]
        mev_potential = random.choice(MEV_POTENTIALS)
        if profitable_txs:
            profitable_txs.sort(key=lambda x: x['mev_potential'], reverse=True)
            for i in range(min(len(profitable_txs), 5)):  # Limit to 5 attempts or less
                target_tx = profitable_txs[i]
                existing_attacks = [tx for tx in mempool_content if tx['gas_fee'] - 2 <= target_tx['gas_fee'] <= tx['gas_fee'] + 2]
                switch_prob = min(0.9, len(existing_attacks) / 10)
                if random.random() >= switch_prob:
                    break

            # launch attack targeting the target transaction
            # determine the attack type (front, back, or sandwich) this will be reflected in the gas fee, +1 for front, -1 for back, one front one back is sandwich
            attack_type = random.choice(['front', 'back', 'sandwich'])
            if attack_type == 'front':
                gas_fee = target_tx['gas_fee'] + 1
                return Transaction(gas_fee, mev_potential, self.id, block_num, target_tx)
            elif attack_type == 'back':
                gas_fee = target_tx['gas_fee'] - 1
                return Transaction(gas_fee, mev_potential, self.id, block_num, target_tx)
            elif attack_type == 'sandwich':
                gas_fee = target_tx['gas_fee'] + 1
                return Transaction(gas_fee, mev_potential, self.id, block_num, target_tx)
            
        # else:
        #     # self.create_transactions(block_num)
        #     # don't create transactions
        #     return None


    def broadcast_transactions(self):
        # for users: they should only have a set of builders they are sending transactions to
        # this should be 80% of the total builders
        # note that users see the mempool of these visible builders
        for builder in self.visible_builders:
            pass

    def test_case_1(self):
        # test if builder can get the broadcassted transactions
        # test if the transactions are correctly added to the mempool


if __name__ == "__main__":
    builders = [Builder() for i in range(5)]
