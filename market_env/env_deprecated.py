# # pylint: disable=missing-module-docstring
# # pylint: disable=missing-class-docstring
# # pylint: disable=missing-function-docstring

# from __future__ import annotations


# class ChainEnv:
#     def __init__(
#         self,
#         users: dict[str, User] | None = None,
#         proposers: dict[str, Proposer] | None = None,
#         builders: dict[str, Builder] | None = None,
#         mempools: Mempool | None = None,
#         blocks: Block | None = None,
#         chains: Chain | None = None,
#     ):

#         if users is None:
#             users = {}
#         if proposers is None:
#             proposers = {}
#         if builders is None:
#             builders = {}
#         if mempools is None:
#             mempools = []
#         if blocks is None:
#             blocks = []
#         if chains is None:
#             chains = []

#         self.users = users
#         self.proposers = proposers
#         self.builders = builders
#         self.mempools = mempools
#         self.blocks = blocks
#         self.chains = chains


# class User:
#     def __init__(self, user_id, env: ChainEnv):
#         self.user_id = user_id
#         self.env = env


# class Mempool:
#     def __init__(
#         self, transaction_id, amount, sender, recipient, gas, gas_price, timestamp
#     ) -> None:
#         self.transaction_id = transaction_id
#         self.amount = amount
#         self.sender = sender
#         self.recipient = recipient
#         self.gas = gas
#         self.gas_price = gas_price
#         self.timestamp = timestamp


# class Proposer:
#     def __init__(self, proposer_id, fee_recipent) -> None:
#         self.proposer_id = proposer_id
#         self.fee_recipent = fee_recipent

#     def select_header(self, blocks: list) -> dict:
#         if not blocks:
#             return None

#         headers = [Block.get_header() in Block]

#         selected_header = max(headers, key=lambda x: x["bid"])
#         self.selected_header = selected_header
#         return selected_header

#     def get_selected_header(self):
#         return self.selected_header


# class Builder:
#     def __init__(self, builder_id) -> None:
#         self.builder_id = builder_id
#         self.mempool = None

#     def order_transactions(self, transactions):
#         ordered_transactions = sorted(transactions, key=lambda x: x.gas, reverse=True)
#         return ordered_transactions

#     def build_block(self, block_id: str, gas_limit: int) -> Block:
#         if self.mempool is None:
#             raise ValueError("Mempool empty")

#         transactions = self.mempool.get_transactions()
#         ordered_transactions = self.order_transactions(transactions)

#         block = Block(block_id)
#         gas_used = 0

#         for transaction in ordered_transactions:
#             # Check if adding the transaction would exceed the gas limit
#             if gas_used + transaction.gas <= gas_limit:
#                 block.add_transaction(transaction)
#                 gas_used += transaction.gas
#             else:
#                 break

#         return block


# class Block:
#     def __init__(
#         self,
#         transaction_id: str,
#         gas: float,
#         gas_price: float,
#         builder_id: str,
#         timestamp: int,
#         user_id: str,
#         fee_recipient: str,
#         block_id: str,
#         header_id: str,
#         bid: float,
#     ) -> None:
#         self.transaction_id = transaction_id
#         self.gas = gas
#         self.gas_price = gas_price
#         self.builder_id = builder_id
#         self.timestamp = timestamp
#         self.user_id = user_id
#         self.fee_recipient = fee_recipient
#         self.block_id = block_id
#         self.header_id = header_id
#         self.bid = bid

#     def get_total_gasPrice(self):
#         return sum(transaction.gas_price for transaction in self.transaction)

#     def get_header(self):
#         total_gas_price = self.get_total_gas()
#         header = {
#             "header_id": self.header_id,
#             "timestamp": self.timestamp,
#             "total_gasPrice": total_gas_price,
#             "fee_recipient": self.fee_recipient,
#             "builder_id": self.builder_id,
#             "bid": self.bid,
#         }
#         return header


# class Chain:
#     def __init__(self, block_id: str) -> None:
#         self.block_id = block_id
