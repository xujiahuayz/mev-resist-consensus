# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring


class ChainEnv:
    def __init__(
        self,
        users: dict[str, User] | None = None,
        proposers: dict[str, Proposer] | None = None,
        builders: dict[str, Builder] | None = None,
        mempool: Mempool | None = None,
        blocks: Block | None = None,
        chains: Chain | None = None,
    ):

        if users is None:
            users = {}
        if proposers is None:
            proposers = {}
        if builders is None:
            builders = {}
        if mempools is None:
            mempools = []
        if blocks is None:
            blocks = []
        if chains is None:
            chains = []

        self.users = users
        self.proposers = proposers
        self.builders = builders
        self.mempools = mempools
        self.blocks = blocks
        self.chains = chains


class User:
    def __init__(self, user_id, env: ChainEnv) -> None:
        self.user_id = user_id
        self.env = env

    # transactions sent to mempool
    def create_transaction(
        self, transaction_id, amount, recipient, gas, timestamp
    ) -> Transaction:
        transaction = Mempool(transaction_id, amount, recipient, gas, timestamp)
        self.env.mempool.add_transaction(transaction)


class Mempool:
    def __init__(self) -> None:
        self.transactions: list[dict] = []

    def add_transaction(
        self,
        transaction_id: int,
        amount: float,
        recipient: str,
        gas: int,
        timestamp: int,
    ) -> None:
        transaction = {
            "transaction_id": transaction_id,
            "amount": amount,
            "recipient": recipient,
            "gas": gas,
            "timestamp": timestamp,
        }
        self.transactions.append(transaction)

    def get_transactions(self) -> list[dict]:
        return self.transactions


class Proposer:
    def __init__(self, proposer_id, fee_recipent) -> None:
        self.proposer_id = proposer_id
        self.fee_recipent = fee_recipent

    def select_header(self, header_id, builder_bids) -> Block:
        selected_header = max(builder_bids, key=lambda bid: bid.pay())
        return selected_header


class Builder:
    def __init__(self, builder_id) -> None:
        self.builder_id = builder_id
        self.mempool = None

    def build_block(self, block_id: str, gas_limit: int) -> Block:
        if self.mempool is None:
            raise ValueError("Mempool empty")

        transactions = self.mempool.get_transactions()
        ordered_transactions = self.order_transactions(transactions)

        block = Block(block_id)
        gas_used = 0

        for transaction in ordered_transactions:
            # Check if adding the transaction would exceed the gas limit
            if gas_used + transaction.gas <= gas_limit:
                block.add_transaction(transaction)
                gas_used += transaction.gas
            else:
                break

        return block

    def order_transacitons(transaction_id, gas):
        pass


class Block:
    pass


class Chain:
    pass
