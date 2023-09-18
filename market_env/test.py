from environment import Chain, Account

def test_chain():
    new_chain = Chain()
    pass

def test_account():
    new_account = Account(100.5)
    new_account.deposit(100.5)
    new_account.withdraw(50.5)
    print(new_account.balance)

def test_node():
    pass

if __name__ == "__main__":
    test_account()