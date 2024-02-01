"""
cron: 1 1 1 1 1
new Env('Web3Go_Mint')
"""
from eth_typing import ChecksumAddress
from web3 import Web3, HTTPProvider
from web3.exceptions import ContractLogicError

from common.task import QLTask
from common.util import log, get_env

TASK_NAME = 'Web3Go_Mint'
FILE_NAME = 'Web3GoWallet.txt'

RPC_NAME = 'WEB3GO_RPC'
rpc = get_env(RPC_NAME)
if rpc is None or rpc == '':
    rpc = "https://bsc-dataseed2.defibit.io"
    log.info(f"暂未设置RPC，默认BNB RPC: {rpc}")

bsc = Web3(HTTPProvider(rpc))

abi = [{"inputs": [{"name": "param_address_1", "type": "address"}], "name": "safeMint", "outputs": [], "type": "function"}]
contract_address = bsc.to_checksum_address('0xa4Aff9170C34c0e38Fed74409F5742617d9E80dc')
contract = bsc.eth.contract(address=contract_address, abi=abi)


def send_mint(address: ChecksumAddress, private_key: str) -> str:
    nonce = bsc.eth.get_transaction_count(address)
    method = contract.functions.safeMint(address)
    try:
        tx = method.build_transaction({'from': address, 'gasPrice': bsc.eth.gas_price, 'nonce': nonce})
    except ContractLogicError as e:
        return str(e)
    signed_tx = bsc.eth.account.sign_transaction(tx, private_key)
    transaction = bsc.eth.send_raw_transaction(signed_tx.rawTransaction)
    bsc.eth.wait_for_transaction_receipt(transaction)
    return transaction.hex()


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        address = bsc.to_checksum_address(split[0])
        private_key = split[1]
        result = send_mint(address, private_key)
        if result.startswith('0x'):
            log.info(f'【{index}】Mint交易Hash: {result}')
        else:
            log.info(f'【{index}】Mint交易失败: {result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
