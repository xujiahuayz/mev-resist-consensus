from blockchain_env.account import Account
from blockchain_env.chain import Block, Chain
from blockchain_env.builder import Builder, Mempool
from blockchain_env.constants import BASE_FEE, GAS_LIMIT
from blockchain_env.proposer import Blockpool, Proposer
from blockchain_env.transaction import Transaction

import random
import uuid

def generate_accounts(num_accounts):
    accounts = []
    for i in range(num_accounts):
        address = f"Address{i}"
        balance = random.uniform(100.0, 1000.0)
        account = Account(address, balance)
        accounts.append(account)
    return accounts

# valid transactions

def generate_transactions(accounts, num_transactions):
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
        proposer = Proposer(address=proposer_address, balance=initial_balance, proposer_strategy="greedy")
        proposers.append(proposer)
    return proposers

def simulate(chain):
    slot:int = 12
    counter = 0
    # generate a random number of transactions
    random_number = random.randint(1, 100)
    while True:
        new_transactions = generate_transactions(chain.accounts, random_number)

        # for each transaction broadcast to a random set of builders
        for transaction in new_transactions:
            broadcasted_builders = random.sample(chain.builders, len(chain.builders) // 2)
            for builder in broadcasted_builders:
                # set a random delay for the time recieving transaction
                enter_time = random.uniform(0, 0.5)  
                builder.mempool.add_transaction(transaction, enter_time)

        if counter % slot == 0:
            # for each builder, select transactions, append bid and add to blockpool
            for builder in chain.builders:
                # select transactions
                selected_transactions = builder.select_transactions()
                # select proposer
                selected_proposer = chain.select_proposer()

                # add a bid for the selected list of transactions
                bid_transaction = builder.bid(selected_proposer.address)
                # update the selected transactions by adding the bid transaction into the selected list of transactions (covered in Body class)
                # selected_transactions = selected_transactions.append(bid_transaction)
                # record the time
                selecte_time = counter
                # add selected transactions as a block to the blockpool for the selected propsoer
                selected_proposer.blockpool.add_body(selected_transactions, selecte_time)
                

                selected_proposer.blockpool.add_body(block, selecte_time)
                selected_body = selected_proposer.select_block()

                if selected_body is not None:
                    confirm_time = random.uniform(0, 0.5)  
                    chain.add_block(selected_body, confirm_time, transaction, selected_proposer.address)
                    selected_proposer.blockpool.remove_body(selected_body)
                    for transaction in selected_body:
                        transaction.confirm(selected_proposer.address, confirm_time)
                        for builder in builders:
                            builder.mempool.remove_transaction(transaction)

        counter += 1
        if counter >= 100:
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
    for transaction in transactions:
        print(
            f"Transaction ID: {transaction.transaction_id}, Sender: {transaction.sender}, "
            f"Recipient: {transaction.recipient}, Amount: {transaction.amount}, "
            f"Base Fee: {transaction.base_fee}, Priority Fee: {transaction.priority_fee}"
        )
    for builder in builders:
        print(builder.address, builder.balance)
    for proposer in proposers:
        print(proposer.address, proposer.balance)

    
