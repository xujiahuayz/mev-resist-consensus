from blockchain_env.account import Account
from blockchain_env.chain import Chain
from blockchain_env.builder import Builder, Mempool
from blockchain_env.constants import BASE_FEE, GAS_LIMIT
from blockchain_env.proposer import Proposer, Blockpool
from blockchain_env.transaction import Transaction
from blockchain_env.block import Block

import random
import uuid
import copy

def generate_accounts(num_accounts):
    accounts = []
    for i in range(num_accounts):
        address = f"Address{i}"
        balance = random.uniform(100.0, 1000.0)
        account = Account(address, balance)
        accounts.append(account)
    return accounts

# valid transactions

# add percentage of invalid transactions
def generate_transactions(accounts, num_transactions, valid_percentage):
    transactions = []
    for _ in range(num_transactions):
        sender_address = random.choice(accounts).address
        recipient_address = random.choice(accounts).address
        if sender_address == recipient_address:
            while True:
                recipient_address = random.choice(accounts).address
                if sender_address != recipient_address:
                    break
        
        transaction_id = str(uuid.uuid4())
        timestamp = None

        gas = 21000
        amount = random.uniform(1.0, 10.0)  
        base_fee = BASE_FEE
        priority_fee = random.uniform(0.0, 5.0)
        transaction = Transaction(
            transaction_id=transaction_id, 
            timestamp=timestamp,
            sender=sender_address, 
            recipient=recipient_address, 
            gas=gas, 
            amount=amount, 
            base_fee=base_fee, 
            priority_fee=priority_fee)
        if transaction is not None:
            transactions.append(transaction)
    return transactions

def generate_builders(num_builders):
    builders = []
    for i in range(num_builders):
        builder = Builder(address=f"Builder{i}", balance=initial_balance, builder_strategy="greedy")
        builders.append(builder)
    return builders

def generate_proposers(num_proposers):
    proposers = []
    for i in range(num_proposers):
        proposer_address = f"Proposer{i}"
        blockpool = Blockpool(address=proposer_address)
        proposer = Proposer(address=proposer_address, balance=initial_balance, proposer_strategy="greedy", blockpool=blockpool)
        proposers.append(proposer)
    return proposers

def simulate(chain):
    slot:int = 12
    counter = 0
    # generate a random number of transactions
    random_number = random.randint(1, 100)
    while True:
        new_transactions = generate_transactions(chain.accounts, random_number, 0.8)

        # for each transaction broadcast to a random set of builders
        for transaction in new_transactions:
            broadcasted_builders = random.sample(chain.builders, len(chain.builders) // 2)
            for builder in broadcasted_builders:
                # set a random delay for the time recieving transaction
                enter_time = random.uniform(0, 1)  
                builder.mempool.add_transaction(transaction, counter+enter_time)

        # for each slot, a block should be built and added on chain
        if counter % slot == 0:
            # for each builder, select transactions, append bid and add to blockpool
            # select proposer for the slot
            selected_proposer = chain.select_proposer()
            for builder in chain.builders:
                # select transactions
                selected_transactions = builder.select_transactions()
                # add a bid for the selected list of transactions
                bid_transaction = builder.bid(selected_proposer.address)
                # update the selected transactions by adding the bid transaction into the selected list of transactions (covered in Body class)
                selected_transactions = selected_transactions.append(copy.deepcopy(bid_transaction))
                
                # record the time
                selecte_time = counter
                # get information (block_id) of previous block
                previous_block_id = chain.find_latest_block()
                # if previous_block is not None:
                #     previous_block_id = previous_block.block_id
                # else:
                #     # Handle the case where there are no previous blocks (e.g., for the first block)
                #     previous_block_id = None

                # calculate total fee
                if selected_transactions:
                    total_fee = sum(transaction.fee for transaction in selected_transactions)
                else:
                    total_fee = 0 
                # create a new block with the selected transactions
                new_block = Block(
                    block_id=uuid.uuid4(),
                    previous_block_id=previous_block_id,
                    timestamp=selecte_time,
                    proposer_address=selected_proposer.address,
                    transactions=selected_transactions,
                    builder_id=builder.address,
                    total_fee=total_fee
                )

                # add the new block to the blockpool
                selected_proposer.blockpool.add_block(new_block, selecte_time)

                # the selected proposer select a block from the blockpool 
                selected_block = selected_proposer.select_block()

                # add the selected block to the longest chain
                if selected_block is not None:
                    confirm_time = counter  
                    chain.add_block(block=selected_block, confirm_time=confirm_time, transaction=transaction, proposer=selected_proposer)
                    selected_proposer.blockpool.remove_block(selected_block)
                    for transaction in selected_block.transactions:
                        transaction.confirm(selected_proposer.address, confirm_time)
                        for builder in builders:
                            builder.mempool.remove_transaction(transaction)

            # balance change for each account after block put on chain
            # for each block, update the balance of proposer and builder e.g. proposer get the trasnaction total fee - bid and builder get the bid
            # for each transaction in the block, update the balance of sender and recipient
            # use the withdraw and deposit method in account class

            # Create a mapping from builder_id to Builder object
            builder_mapping = {builder.address: builder for builder in chain.builders}

            for selected_block in chain.blocks:
                proposer = selected_proposer
                builder = selected_block.builder_id
                # using the mapping get the builder object from the builder_id
                builder = builder_mapping.get(builder)
                proposer.deposit(selected_block.total_fee - bid_transaction.amount)
                builder.deposit(bid_transaction.amount)
                for transaction in selected_block.transactions:
                    sender = transaction.sender
                    recipient = transaction.recipient
                    sender.withdraw(transaction.amount)
                    recipient.deposit(transaction.amount-transaction.fee)

        counter += 1
        if counter >= 10:
            break
                

if __name__ == "__main__":

    num_accounts = 200
    num_transactions = 100
    initial_balance = 100.0
    num_builders = 20
    num_proposers = 20

    chain = Chain()

    accounts = generate_accounts(num_accounts)
    builders = generate_builders(num_builders)
    proposers = generate_proposers(num_proposers)

    chain.proposers = proposers
    chain.builders = builders
    chain.accounts = accounts

    simulate(chain)

    for account in accounts:
        print(account.address, account.balance)

    for builder in builders:
        print(builder.address, builder.balance)

    for proposer in proposers:
        print(proposer.address, proposer.balance)

    for selected_block in chain.blocks:
        print(f"Block Header ID: {selected_block.block_id}")
        print(f"Previous Block Header ID: {selected_block.previous_block_id}")
        print(f"Total Fee: {selected_block.total_fee}")
        
        # Get the bid transaction
        bid_transaction = None
        for transaction in selected_block.transactions:
            if transaction.sender == selected_block.builder_id:
                bid_transaction = transaction
                break

        if bid_transaction:
            print(f"Bid Amount: {bid_transaction.amount}")
        else:
            print("No Bid Transaction found in this block")

        print(f"Proposer: {selected_block.proposer_address}")
        print(f"Builder ID: {selected_block.builder_id}")

        print("Transactions:")
        for transaction in selected_block.transactions:
            print(f"  Transaction ID: {transaction.transaction_id}")
            print(f"  Sender: {transaction.sender}")
            print(f"  Recipient: {transaction.recipient}")
            print(f"  Gas: {transaction.gas}")
            print(f"  Amount: {transaction.amount}")
            print(f"  Base Fee: {transaction.base_fee}")
            print(f"  Priority Fee: {transaction.priority_fee}")
            print(f"  Fee: {transaction.fee}")
            print(f"  Timestamp: {transaction.timestamp}")
            print()

        print()

