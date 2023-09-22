from environment import Chain, Account, Node, Mempool, Transaction, Builder, Proposer
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


if __name__ == "__main__":
    test_account()
