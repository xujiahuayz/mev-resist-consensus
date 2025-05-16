import random
from blockchain_env.transaction import Transaction
from copy import deepcopy
from blockchain_env.network import Node 
from typing import List

BLOCK_CAP: int = 100

class Builder(Node):
    def __init__(self, builder_id: int, is_attacker: bool) -> None:
        super().__init__(builder_id)
        self.is_attacker: bool = is_attacker
        self.balance: int = 0
        self.selected_transactions: List[Transaction] = []

    def launch_attack(self, block_num: int, target_transaction: Transaction, attack_type: str) -> Transaction:
        # Launch an attack with specific gas fee and mev potential, targeting a specific transaction
        if attack_type == 'front':
            gas_fee: int = target_transaction.gas_fee + 1
        else:  # back
            gas_fee: int = target_transaction.gas_fee - 1
            
        mev_potential: int = 0  # Attack transactions don't have MEV potential themselves
        creator_id: int = self.id
        created_at: int = block_num
        target_tx: Transaction = target_transaction

        # Create the attack transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction: Transaction) -> None:
        # Builder receives transaction and adds to mempool
        if transaction not in self.mempool:  # Avoid duplicates
            self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num: int) -> List[Transaction]:
        selected_transactions: List[Transaction] = []
        if self.is_attacker:
            # Sort transactions by mev potential + gas fee for attackers
            self.mempool.sort(key=lambda x: x.mev_potential + x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) >= BLOCK_CAP:
                    break
                    
                if transaction.mev_potential > 0:
                    attack_type: str = random.choice(['front', 'back'])
                    attack_transaction: Transaction = self.launch_attack(block_num, transaction, attack_type)

                    if attack_type == 'front':
                        selected_transactions.append(attack_transaction)
                        if len(selected_transactions) < BLOCK_CAP:
                            selected_transactions.append(transaction)
                    elif attack_type == 'back':
                        selected_transactions.append(transaction)
                        if len(selected_transactions) < BLOCK_CAP:
                            selected_transactions.append(attack_transaction)
                else:
                    selected_transactions.append(transaction)
        else:
            # Sort transactions by gas fee for non-attackers
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) >= BLOCK_CAP:
                    break
                selected_transactions.append(transaction)

        return selected_transactions

    def bid(self, selected_transactions: List[Transaction]) -> float:
        total_gas_fee: float = sum(tx.gas_fee for tx in selected_transactions)
        
        # Initial block value is based on total gas fee
        block_value: float = total_gas_fee
        
        # Check if the builder is an attacker and has launched any attack
        if self.is_attacker:
            # Sum the MEV potential of targeted transactions if any attacks are launched
            mev_gain: float = sum(tx.target_tx.mev_potential for tx in selected_transactions if tx.target_tx)
            block_value += mev_gain  # Add MEV profit to block value for attackers

        # Initial bid is a random percentage of the block value between 40% and 60%
        bid: float = block_value * random.uniform(0.4, 0.6)

        # Reactive strategy over 5 rounds of bidding
        for _ in range(5):
            # Get current highest bid from history in the builder's mempool
            # Use the actual block values (gas fees + MEV) instead of just gas fees
            block_values: List[float] = []
            for tx in self.mempool:
                tx_value = tx.gas_fee
                if hasattr(tx, 'target_tx') and tx.target_tx:
                    tx_value += tx.target_tx.mev_potential
                block_values.append(tx_value)
            
            if len(block_values) == 0:
                break  # If no transactions in the mempool, exit the loop

            highest_value: float = max(block_values)
            
            if highest_value > bid:
                # Increase bid by 0.1 times the highest value
                bid = min(highest_value, bid + 0.1 * highest_value)
            else:
                # Get the second highest value if possible, else use the current bid
                sorted_values: List[float] = sorted(block_values, reverse=True)
                if len(sorted_values) > 1:
                    second_highest_value: float = sorted_values[1]
                    bid = max(0.5 * (highest_value + second_highest_value), bid)
                else:
                    bid = max(0.5 * highest_value, bid)

        # Add a small random factor to prevent identical bids
        bid = bid * random.uniform(0.99, 1.01)

        return bid

    def get_mempool(self) -> List[Transaction]:
        return self.mempool
    
    def clear_mempool(self, block_num: int) -> None:
        # clear any transsaction that is already included onchain, and also clear pending transactions that has been in mempool for too long
        timer: int = block_num - 5
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at < timer]


