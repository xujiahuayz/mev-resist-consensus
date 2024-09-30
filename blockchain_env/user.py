import random
from copy import deepcopy
from blockchain_env.constants import SAMPLE_GAS_FEES, MEV_POTENTIALS
from blockchain_env.transaction import Transaction

random.seed(16)

class User:
    def __init__(self, user_id, is_attacker, builders):
        self.id = user_id
        self.is_attacker = is_attacker
        # Initialize visible builders, which is 80% of the total builders
        self.visible_builders = random.sample(builders, int(0.8 * len(builders)))
        self.balance = 0

    def create_transactions(self, block_num):
        # Create a normal transaction with random gas fee and mev potential from the sample list
        gas_fee = random.choice(SAMPLE_GAS_FEES)
        mev_potential = random.choice(MEV_POTENTIALS)
        creator_id = self.id
        created_at = block_num
        target_tx = None
        return Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        
    def launch_attack(self, block_num):
        # Launch front, back, or sandwich attack on the transaction with the highest MEV potential
        # Get the mempool content from the visible builders
        mempool_content = []
        for builder in self.visible_builders:
            mempool_content.extend(deepcopy(builder.get_mempool())) 

        # Filter for transactions with MEV potential greater than zero
        profitable_txs = [tx for tx in mempool_content if tx.mev_potential > 0]
        if profitable_txs:
            # Sort by highest MEV potential
            profitable_txs.sort(key=lambda x: x.mev_potential, reverse=True)
            for i in range(min(len(profitable_txs), 5)):  # Limit to 5 attempts or less
                target_tx = profitable_txs[i]
                # Look for existing attacks by comparing gas fees
                existing_attacks = [tx for tx in mempool_content if tx.gas_fee - 2 <= target_tx.gas_fee <= tx.gas_fee + 2]
                # Calculate switch probability based on the number of existing attacks
                switch_prob = min(0.9, len(existing_attacks) / 10)
                if random.random() >= switch_prob:
                    break

            # Determine attack type (front, back, sandwich) and adjust the gas fee accordingly
            attack_type = random.choice(['front', 'back'])
            if attack_type == 'front':
                gas_fee = target_tx.gas_fee + 1
                return Transaction(gas_fee, 0, self.id, block_num, target_tx)  # Front-run attack
            elif attack_type == 'back':
                gas_fee = target_tx.gas_fee - 1
                return Transaction(gas_fee, 0, self.id, block_num, target_tx)  # Back-run attack
            
        # If no profitable transaction is found, create a benign transaction
        return self.create_transactions(block_num)

    def broadcast_transactions(self, transaction):
        # Broadcast transactions to all visible builders
        for builder in self.visible_builders:
            builder.receive_transaction(transaction)
