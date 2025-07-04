"""Builder module for blockchain environment."""

import random
from copy import deepcopy
from typing import List

from blockchain_env.transaction import Transaction
from blockchain_env.network import Node

BLOCK_CAP: int = 100

class Builder(Node):
    """Builder class with attack and bidding logic."""
    def __init__(self, builder_id: int, is_attacker: bool) -> None:
        """Initialize a Builder."""
        super().__init__(builder_id)
        self.is_attacker: bool = is_attacker
        self.balance: int = 0
        self.selected_transactions: List[Transaction] = []

    def launch_attack(self, block_num: int, target_transaction: Transaction, attack_type: str) -> Transaction:
        """Launch an attack transaction targeting a specific transaction."""
        if attack_type == 'front':
            gas_fee: int = target_transaction.gas_fee + 1
        else:
            gas_fee: int = target_transaction.gas_fee - 1
        mev_potential: int = 0
        creator_id: int = self.id
        created_at: int = block_num
        target_tx: Transaction = target_transaction
        attack_transaction = Transaction(gas_fee, mev_potential, creator_id, created_at, target_tx)
        attack_transaction.attack_type = attack_type
        return attack_transaction

    def receive_transaction(self, transaction: Transaction) -> None:
        """Receive a transaction and add to mempool if not duplicate."""
        if transaction not in self.mempool:
            self.mempool.append(deepcopy(transaction))

    def select_transactions(self, block_num: int) -> List[Transaction]:
        """Select transactions for block proposal."""
        selected_transactions: List[Transaction] = []
        if self.is_attacker:
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
            self.mempool.sort(key=lambda x: x.gas_fee, reverse=True)
            for transaction in self.mempool:
                if len(selected_transactions) >= BLOCK_CAP:
                    break
                selected_transactions.append(transaction)
        return selected_transactions

    def bid(self, selected_transactions: List[Transaction]) -> float:
        """Calculate the builder's bid for the block."""
        total_gas_fee: float = sum(tx.gas_fee for tx in selected_transactions)
        block_value: float = total_gas_fee
        if self.is_attacker:
            mev_gain: float = sum(tx.target_tx.mev_potential for tx in selected_transactions if hasattr(tx, 'target_tx') and tx.target_tx)
            block_value += mev_gain
        bid: float = block_value * random.uniform(0.4, 0.6)
        for _ in range(5):
            block_values: List[float] = []
            for tx in self.mempool:
                tx_value = tx.gas_fee
                if hasattr(tx, 'target_tx') and tx.target_tx:
                    tx_value += tx.target_tx.mev_potential
                block_values.append(tx_value)
            if not block_values:
                break
            highest_value: float = max(block_values)
            if highest_value > bid:
                bid = min(highest_value, bid + 0.1 * highest_value)
            else:
                sorted_values: List[float] = sorted(block_values, reverse=True)
                if len(sorted_values) > 1:
                    second_highest_value: float = sorted_values[1]
                    bid = max(0.5 * (highest_value + second_highest_value), bid)
                else:
                    bid = max(0.5 * highest_value, bid)
        bid = bid * random.uniform(0.99, 1.01)
        return bid

    def get_mempool(self) -> List[Transaction]:
        """Get the builder's mempool."""
        return self.mempool

    def clear_mempool(self, block_num: int) -> None:
        """Clear transactions included onchain or too old from the mempool."""
        timer: int = block_num - 5
        self.mempool = [tx for tx in self.mempool if tx.included_at is None and tx.created_at < timer]
