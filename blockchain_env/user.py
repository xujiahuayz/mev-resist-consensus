import random

from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS

random.seed(16)

BLOCKNUM = 50

class User:
    def __init__(self, user_id, is_attacker):
        self.id = user_id
        self.is_attacker = is_attacker 
        self.transactions = []
        self.gas_fee = 0
        self.mempool = []

    def create_transactions(self, block_num):
        # create normal trasnctions with random gas fee and mev potential from the sample list
        gas_fee = random.choice(SAMPLE_GAS_FEES)
        mev_potential = random.choice(MEV_POTENTIALS)
        creator_id = self.id
        created_at = block_num
        self.transactions.append((gas_fee, mev_potential, creator_id, created_at))

    def launch_attack(self, block_num):
        # if there are profitable transctions in the mempool, user can launch attack
        # the attack could be front, back, or sandwich attack (let this be random)
        # attack the transaction with highest mev potential (if you see that there are already a lot transactions taregting the same transaction, try to attack another one)
        # other attack transactions could be spotted by seeing that gas fee is similar to the target transaction
        # the more they see others attacking the same transaction, the more likely they are to attack the same transaction
        # if no transactions are with non zero mev potential, just create benign transactions
        profitable_txs = [tx for tx in self.mempool if tx['mev_potential'] > 0]
        mev_potential = random.choice(MEV_POTENTIALS)
        if profitable_txs:
            profitable_txs.sort(key=lambda x: x['mev_potential'], reverse=True)
            for i in range(min(len(profitable_txs), 5)):  # Limit to 5 attempts or less
                target_tx = profitable_txs[i]
                existing_attacks = [tx for tx in self.mempool if tx['gas_fee'] - 2 <= target_tx['gas_fee'] <= tx['gas_fee'] + 2]
                switch_prob = min(0.9, len(existing_attacks) / 10)
                if random.random() >= switch_prob:
                    break

            # launch attack targeting the target transaction
            # determine the attack type (front, back, or sandwich) this will be reflected in the gas fee, +1 for front, -1 for back, one front one back is sandwich
            attack_type = random.choice(['front', 'back', 'sandwich'])
            if attack_type == 'front':
                gas_fee = target_tx['gas_fee'] + 1
                self.transactions.append((gas_fee, mev_potential, self.id, target_tx['created_at']))
            elif attack_type == 'back':
                gas_fee = target_tx['gas_fee'] - 1
                self.transactions.append((gas_fee, mev_potential, self.id, target_tx['created_at']))
            elif attack_type == 'sandwich':
                gas_fee = target_tx['gas_fee'] + 1
                self.transactions.append((gas_fee, mev_potential, self.id, target_tx['created_at']))
                gas_fee = target_tx['gas_fee'] - 1
                self.transactions.append((gas_fee, mev_potential, self.id, target_tx['created_at']))

        else:
            self.create_transactions(block_num)


    def broadcast_transactions(self, builders):
        # for users: they should only have a set of builders they are sending transactions to
        # this should be 80% of the total builders
        # note that users see the mempool of these visible builders
        visible_builders = random.sample(builders, int(0.8 * len(builders)))
        for builder in visible_builders:
            for tx in self.transactions:
                builder.receive_transaction(tx)
            self.mempool.extend(builder.get_mempool())


    def test_case_1(self):
        # test how the user's transactions are distributed across builders
        # Create two users: one normal and one attacker
        # The User class takes two parameters: user_id and is_attacker
        normal_user = User(0, is_attacker=False)
        attacker = User(1, is_attacker=True)

        # Create a list of mock builders
        builders = [MockBuilder() for _ in range(5)]

        # Simulate a block where transactions are created
        block_num = 1

        # Normal user creates transactions
        normal_user.create_transactions(block_num)

        # Attacker launches an attack
        attacker.launch_attack(block_num)

        # Both users broadcast their transactions
        normal_user.broadcast_transactions(builders)
        attacker.broadcast_transactions(builders)

        # Check the distribution of transactions across builders
        for i, builder in enumerate(builders):
            print(f"Builder {i} mempool size: {len(builder.get_mempool())}")

        # Check the types of transactions in the mempool
        all_txs = [tx for builder in builders for tx in builder.get_mempool()]
        normal_txs = [tx for tx in all_txs if tx[2] == 0]  # transactions from normal user
        attack_txs = [tx for tx in all_txs if tx[2] == 1]  # transactions from attacker

        print(f"Total transactions: {len(all_txs)}")
        print(f"Normal transactions: {len(normal_txs)}")
        print(f"Attack transactions: {len(attack_txs)}")

        return len(all_txs), len(normal_txs), len(attack_txs)

class MockBuilder:
    def __init__(self):
        self.mempool = []

    def receive_transaction(self, tx):
        self.mempool.append(tx)

    def get_mempool(self):
        return self.mempool

if __name__ == "__main__":
    test_case_1()