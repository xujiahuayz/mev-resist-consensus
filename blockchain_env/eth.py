from web3 import Web3

KEY = 'GqNbzR4hweWoLJJ8pTZEe7NaTSbwrq2N'

alchemy_url = f'https://eth-mainnet.alchemyapi.io/v2/{KEY}'

web3 = Web3(Web3.HTTPProvider(alchemy_url))

print(web3.is_connected())

HASH = '<TRANSACTION_HASH>'

# try:
#     # Get transaction by hash
#     transaction = web3.eth.get_transaction(HASH)
#     # Get transaction receipt to find the gas used
#     receipt = web3.eth.get_transaction_receipt(HASH)
    
#     # Calculate the transaction fee (Gas Used * Gas Price)
#     transaction_fee = receipt['gasUsed'] * transaction['gasPrice']
    