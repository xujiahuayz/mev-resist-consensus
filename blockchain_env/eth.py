from web3 import Web3

alchemy_api_key = 'GqNbzR4hweWoLJJ8pTZEe7NaTSbwrq2N'

alchemy_url = f'https://eth-mainnet.alchemyapi.io/v2/{alchemy_api_key}'

web3 = Web3(Web3.HTTPProvider(alchemy_url))

print(web3.is_connected())

transaction_hash = '<TRANSACTION_HASH>'

try:
    # Get transaction by hash
    transaction = web3.eth.get_transaction(transaction_hash)
    # Get transaction receipt to find the gas used
    receipt = web3.eth.get_transaction_receipt(transaction_hash)
    
    # Calculate the transaction fee (Gas Used * Gas Price)
    transaction_fee = receipt['gasUsed'] * transaction['gasPrice']
    
    # Convert the transaction fee from wei to ether
    transaction_fee_ether = web3.fromWei(transaction_fee, 'ether')
    
    print(f"Transaction Fee in Ether: {transaction_fee_ether}")
except Exception as e:
    print(f"An error occurred: {e}")