"""
cron: 0 10 * * *
new Env('Zeta_交互')
"""
import time

from eth_typing import ChecksumAddress
from tls_client import Session
from web3 import Web3, HTTPProvider

from common.task import QLTask
from common.util import log, get_env, get_chrome_session, get_error_msg

TASK_NAME = 'Zeta_交互'
FILE_NAME = 'ZetaWallet.txt'

RPC_NAME = 'Zeta_RPC'
rpc = get_env(RPC_NAME)
if rpc is None or rpc == '':
    rpc = "https://zetachain-evm.blockpi.network/v1/rpc/public"
    log.info(f"暂未设置RPC，默认RPC: {rpc}")

zeta = Web3(HTTPProvider(rpc))


def send_zeta(address: ChecksumAddress, private_key: str) -> str:
    nonce = zeta.eth.get_transaction_count(address)
    gas_price = zeta.eth.gas_price
    tx = {'from': address, 'to': address, 'value': Web3.to_wei(0.01, 'ether'), 'nonce': nonce, 'chainId': zeta.eth.chain_id,
          'maxFeePerGas': int(gas_price * 1.2), 'maxPriorityFeePerGas': int(gas_price * 1.1)}
    tx['gas'] = zeta.eth.estimate_gas(tx)
    signed_tx = zeta.eth.account.sign_transaction(tx, private_key)
    transaction = zeta.eth.send_raw_transaction(signed_tx.rawTransaction)
    zeta.eth.wait_for_transaction_receipt(transaction)
    return transaction.hex()


def claim_xp(session: Session, task: str, address: ChecksumAddress, private_key: str) -> str:
    name = f'领取XP-{task}'
    signature = zeta.eth.account.sign_typed_data(private_key, {'name': "Hub/XP", 'version': "1", 'chainId': '7000'},
                                                 {'Message': [{'name': "content", 'type': "string"}]}, {'content': "Claim XP"})
    payload = {"address": address, "task": task, "signedMessage": signature.signature.hex()}
    res = session.post('https://xp.cl04.zetachain.com/v1/xp/claim-task', json=payload)
    if res.text.count('totalXp'):
        return f'{name}: 成功'
    if res.text.count('Task already claimed'):
        return f'{name}: Task already claimed'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        address = zeta.to_checksum_address(split[0])
        private_key = split[1]

        headers = {
            'sec-ch-ua-platform': '"Windows"',
            'Origin': 'https://hub.zetachain.com',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }
        session = get_chrome_session()
        session.headers.update(headers)
        session.proxies = proxy

        result = send_zeta(address, private_key)
        log.info(f'【{index}】交易Hash: {result}   10S后领取XP')
        time.sleep(10)
        result = claim_xp(session, 'SEND_ZETA', address, private_key)
        log.info(f'【{index}】{result}')
        result = claim_xp(session, 'RECEIVE_ZETA', address, private_key)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
