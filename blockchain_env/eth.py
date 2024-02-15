from web3 import Web3

alchemy_api_key = 'GqNbzR4hweWoLJJ8pTZEe7NaTSbwrq2N'

alchemy_url = f'https://eth-mainnet.alchemyapi.io/v2/{alchemy_api_key}'

web3 = Web3(Web3.HTTPProvider(alchemy_url))

print(web3.is_connected())