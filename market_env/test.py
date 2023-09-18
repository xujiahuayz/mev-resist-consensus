from environment import Chain, Account

def test_chain():
    new_chain = Chain()
    pass

def test_account():
    new_account = Account("new_account", 100.5)
    new_account.deposit(100.5)
    new_account.withdraw(50.5)
    print(new_account.balance)

def test_transaction():
    acc1 = Account("wallet_1", 100) 
    acc2 = Account("wallet_2", 50)
    acc1.create_transaction(1, acc2, 10, 1, 1, 10, 1234567890)
    print(acc1.balance)
    print(acc2.balance)

def test_node():
    pass

if __name__ == "__main__":
    test_transaction()