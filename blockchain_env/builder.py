import random
from blockchain_env.transaction import Transaction

BLOCK_CAP = 100

class Builder:
    def __init__(self, builder_id, is_attacker):
        self.id = builder_id
        self.is_attacker = is_attacker
        self.balance = 0
        self.mempool = []
        self.selected_transactions = []

    def launch_attack(self, block_num, target_transaction, attack_type):
        # Launch an attack with specific gas fee and mev potential, targeting a specific transaction
        mev_potential = 0
        gas_fee = target_transaction.gas_fee
        if attack_type == 'front':
            gas_fee += 1
        elif attack_type == 'back':
            gas_fee -= 1

        creator_id = self.id
        created_at = block_num
        target_tx = target_transaction

        # Create the attack transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction):
        # Builder receives transaction and adds to mempool
        self.mempool.append(transaction)

    def select_transactions(self, block_num):
        selected_transactions = []
        if self.is_attacker:
            # Sort transactions by mev potential + gas fee for attackers
            self.mempool.sort(key=lambda x: x.mev_potential + x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    if transaction.mev_potential > 0:
                        attack_type = random.choice(['front', 'back'])
                        attack_transaction = self.launch_attack(block_num, transaction, attack_type)

                        if attack_type == 'front':
                            selected_transactions.append(attack_transaction)
                            selected_transactions.append(transaction)
                        elif attack_type == 'back':
                            selected_transactions.append(transaction)
                            selected_transactions.append(attack_transaction)

                        if len(selected_transactions) > BLOCK_CAP:
                            selected_transactions.pop()
                    else:
                        selected_transactions.append(transaction)
        else:
            # Sort transactions by gas fee for non-attackers
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    selected_transactions.append(transaction)

        return selected_transactions

    def bid(self, selected_transactions):
        total_gas_fee = sum(tx.gas_fee for tx in selected_transactions)
        block_value = total_gas_fee  # Assuming block value is based on total gas fee

        # Initial bid is 50% of block value
        bid = 0.5 * block_value

        # Reactive strategy over 5 rounds of bidding
        for _ in range(5):
            # Get current highest bid from history
            highest_bid = max([tx.gas_fee for tx in self.mempool])
            if highest_bid > bid:
                # Increase bid by 0.1 times the highest bid
                bid = min(highest_bid, bid + 0.1 * highest_bid)
            else:
                # Get the second highest bid
                second_highest_bid = sorted([tx.gas_fee for tx in self.mempool], reverse=True)[1]
                bid = max(0.5 * (highest_bid + second_highest_bid), bid)

        # Return the final bid for this builder
        return bid

    def get_mempool(self):
        return self.mempool


