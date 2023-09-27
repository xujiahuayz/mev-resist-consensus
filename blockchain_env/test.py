from blockchain_env.account import Account
from blockchain_env.chain import Block, Chain
from blockchain_env.builder import Builder, Mempool
from blockchain_env.constants import BASE_FEE, GAS_LIMIT
from blockchain_env.proposer import Blockpool, Proposer
import time

def test_chain():
    new_chain = Chain()
    pass

def test_account():
    new_account = Account("new_account", 100.5)
    new_account.deposit(100.5)
    new_account.withdraw(50.5)
    print(new_account.balance)

    acc1 = Account("wallet_1", 100)
    acc2 = Account("wallet_2", 50)
    acc1.create_transaction(1, acc2, 10, 1, 2, 3, 1234567890)
    print(acc1.balance)
    print(acc2.balance)

def test_node():
    node1 = Node()
    node2 = Node()
    node3 = Node()
    node1.add_peer(node2)
    node1.add_peer(node3)
    print(repr(node1.peers))
    pass

def test_mempool():
    # Create some mock transactions
    transaction1 = Transaction(1, 'wallet_1', 'Bob', 10.0, 1, 1, 21000, 1234567890)
    transaction2 = Transaction(2, 'wallet_2', 'Dave', 20.0, 1, 1, 21000, 1234567891)

    my_mempool = Mempool()

    # Test adding transactions
    my_mempool.add_transaction(transaction1)
    my_mempool.add_transaction(transaction2)
    print(my_mempool.transactions)

    # Test removing a transaction
    my_mempool.remove_transaction(transaction1)
    print(my_mempool)

def test_builder():
    chain = Chain()
    builder = Builder("Builder1", 1000, chain)

    transaction_id_1 = "txn001"
    sender_1 = "sender_address_1"
    recipient_1 = "recipient_address_1"
    amount_1 = 100
    timestamp_1 = time.time()

    transaction_id_2 = "txn002"
    sender_2 = "sender_address_2"
    recipient_2 = "recipient_address_2"
    amount_2 = 150
    timestamp_2 = time.time() + 1

    tx1 = Transaction(
    transaction_id=transaction_id_1,
    sender=sender_1,
    recipient=recipient_1,
    amount=amount_1,
    base_fee=10,
    priority_fee=5,
    gas=300,
    timestamp=timestamp_1
)

    tx2 = Transaction(
    transaction_id=transaction_id_2,
    sender=sender_2,
    recipient=recipient_2,
    amount=amount_2,
    base_fee=10,
    priority_fee=6,
    gas=200,
    timestamp=timestamp_2
)

    builder.mempool.add_transaction(tx1)
    builder.mempool.add_transaction(tx2)

    # Build the block
    block = builder.build_block()

    # Print block details for verification
    print(f"Built block header ID: {block.header_id}")
    print(f"Total transaction fee of block: {block.total_fee}")

def test_find_latest_block():
    chain1 = Chain(
        blocks=[Block(1, 0), Block(2, 1), Block(3, 2), Block(0, None), Block(4, 3), Block(5, 4), Block(102, 101), Block(100, 2), Block(101, 100),
                Block(1002, 101), Block(1003, 1002)]
    )
    print(chain1.find_latest_block())
    # [Block(1, 0), Block(2, 1), Block(3, 2), Block(0, None), Block(4, 3), Block(5, 4), Block(102, 101), Block(100, 2), Block(101, 100), Block(1002, 101), Block(1003, 1002)]

    # 0->1->2->3->4->5
    # 0->1->2->100->101->102
    # 0->1->2->100->101->1002->1003

    # {0: False, 1: False, 2: False, 3: False, 4: False, 5: False, 102: False, 100: False, 101: False, 1002: False, 1003: False}
    # {0: [0]; 1: [1]; 2: [2]; 3: [3]; 4: [4]; 5: [5]; 102: [102]; 100: [100]; 101: [101]; 1002: [1002]; 1003: [1003]}

def test_flow():
    account1 = Account("Address1", 1000.0)
    account2 = Account("Address2", 1000.0)
    mempool = Mempool()
    builder = Builder("Builder1", 100.0, mempSool=mempool)
    blockpool = Blockpool()
    proposer = Proposer("Proposer1", 100.0, blockpool=blockpool)
    chain = Chain(accounts=[account1, account2], builders=[builder], proposers=[proposer])

    transaction = account1.create_transaction(account2.address, 50.0)
    mempool.add_transaction(transaction)
    selected_transaction = builder.select_transactions()[0]

    bid_transaction = builder.bid()
    selected_transaction.amount += bid_transaction.amount

    # Create a body with the selected transaction and append the bid transaction
    body = [selected_transaction, bid_transaction]

    # Add the body to the proposer's blockpool
    proposer.blockpool.add_body(body)

    # Select a block from the proposer's blockpool
    selected_body = proposer.select_block()

    # Add the selected block to the chain
    chain.add_block(selected_body)

    # Check if the chain contains the selected block
    assert selected_body in chain.blocks

if __name__ == "__main__":
    test_flow()