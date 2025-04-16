import random
from blockchain_env.transaction import Transaction
from copy import deepcopy
from blockchain_env.node import Node 
from typing import List

BLOCK_CAP: int = 100

class Builder(Node):
    def __init__(self, builder_id: int, is_attacker: bool) -> None:
        super().__init__(builder_id)
        self.id: int = builder_id
        self.is_attacker: bool = is_attacker
        self.balance: int = 0
        self.mempool: List[Transaction] = []
        self.selected_transactions: List[Transaction] = []

    def launch_attack(self, block_num: int, target_transaction: Transaction, attack_type: str) -> Transaction:
        # Launch an attack with specific gas fee and mev potential, targeting a specific transaction
        mev_potential: int = 0
        gas_fee: int = 0

        creator_id: int = self.id
        created_at: int = block_num
        target_tx: Transaction = target_transaction

        # Create the attack transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction: Transaction) -> None:
        # Builder receives transaction and adds to mempool
        self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num: int) -> List[Transaction]:
        selected_transactions: List[Transaction] = []
        if self.is_attacker:
            # Sort transactions by mev potential + gas fee for attackers
            self.mempool.sort(key=lambda x: x.mev_potential + x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) < BLOCK_CAP:
                    if transaction.mev_potential > 0:
                        attack_type: str = random.choice(['front', 'back'])
                        attack_transaction: Transaction = self.launch_attack(block_num, transaction, attack_type)

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

    def bid(self, selected_transactions: List[Transaction]) -> float:
        total_gas_fee: float = sum(tx.gas_fee for tx in selected_transactions)
        
        # Initial block value is based on total gas fee
        block_value: float = total_gas_fee
        
        # Check if the builder is an attacker and has launched any attack
        if self.is_attacker:
            # Sum the MEV potential of targeted transactions if any attacks are launched
            mev_gain: float = sum(tx.target_tx.mev_potential for tx in selected_transactions if tx.target_tx)
            block_value += mev_gain  # Add MEV profit to block value for attackers

        # Initial bid is 50% of the adjusted block value
        bid: float = 0.5 * block_value

        # Reactive strategy over 5 rounds of bidding
        for _ in range(5):
            # Get current highest bid from history in the builder's mempool
            gas_fees: List[float] = [tx.gas_fee for tx in self.mempool]
            if len(gas_fees) == 0:
                break  # If no transactions in the mempool, exit the loop

            highest_bid: float = max(gas_fees)
            
            if highest_bid > bid:
                # Increase bid by 0.1 times the highest bid
                bid = min(highest_bid, bid + 0.1 * highest_bid)
            else:
                # Get the second highest bid if possible, else use the current bid
                sorted_bids: List[float] = sorted(gas_fees, reverse=True)
                if len(sorted_bids) > 1:
                    second_highest_bid: float = sorted_bids[1]
                    bid = max(0.5 * (highest_bid + second_highest_bid), bid)
                else:
                    bid = max(0.5 * highest_bid, bid)

        # Return the final bid for this builder
        return bid

    def get_mempool(self) -> List[Transaction]:
        return self.mempool
    
    def clear_mempool(self, block_num: int) -> None:
        # clear any transsaction that is already included onchain, and also clear pending transactions that has been in mempool for too long
        timer: int = block_num - 5
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at < timer]


