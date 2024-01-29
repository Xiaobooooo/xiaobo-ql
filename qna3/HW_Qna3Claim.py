"""
cron: 0 0 1 1/1 *
new Env('Qna3领取')
"""
import time

from eth_typing import ChecksumAddress
from tls_client import Session
from web3 import Web3, HTTPProvider

from common.task import QLTask
from common.util import log, get_chrome_session, get_error_msg
from HW_Qna3CheckIn import login, contract_address

TASK_NAME = 'Qna3领取'
FILE_NAME = 'Qna3Wallet.txt'

bsc = Web3(HTTPProvider("https://bsc-dataseed2.defibit.io"))


def claim_all(session: Session):
    name = '获取领取signature'
    res = session.post('https://api.qna3.ai/api/v2/my/claim-all', json={})
    if res.text.count('signature'):
        amount = res.json().get('data').get("amount")
        history_id = res.json().get('data').get("history_id")
        nonce = res.json().get('data').get("signature").get("nonce")
        signature = res.json().get('data').get("signature").get("signature")
        return amount, history_id, nonce, signature
    if res.text.count('statusCode') and res.json().get("statusCode") == 200:
        return None, None, None, None
    return get_error_msg(name, res)


def send_claim(address: ChecksumAddress, private_key: str, claim_amount, claim_nonce, claim_signature) -> (str, int):
    transaction_data = f'0x624f82f5{format(claim_amount, "0>64x")}{format(claim_nonce, "0>64x")}00000000000000000000000000000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000041{claim_signature[2:]}00000000000000000000000000000000000000000000000000000000000000'
    tx_to_estimate = {'from': address, 'to': contract_address, 'data': transaction_data}
    gas = bsc.eth.estimate_gas(tx_to_estimate)
    nonce = bsc.eth.get_transaction_count(address)
    tx = {'to': contract_address, 'value': 0, 'data': transaction_data, 'gasPrice': bsc.eth.gas_price, 'gas': gas, 'nonce': nonce}
    signed_tx = bsc.eth.account.sign_transaction(tx, private_key)
    transaction = bsc.eth.send_raw_transaction(signed_tx.rawTransaction)
    block_number = bsc.eth.wait_for_transaction_receipt(transaction).blockNumber
    return transaction.hex(), block_number


def claim(session: Session, history_id, tx_hash) -> str:
    name = '领取'
    payload = {"hash": tx_hash}
    res = session.put(f'https://api.qna3.ai/api/v2/my/claim/{history_id}', json=payload)
    if res.text.count('statusCode') and res.json().get("statusCode") == 200:
        return f'{name}: 成功'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        address = bsc.to_checksum_address(split[0])
        private_key = split[1]

        session = get_chrome_session()
        session.proxies = proxy
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }
        session.headers.update(headers)
        token = login(session, address, private_key)
        log.info(f'【{index}】登录: 成功')
        session.headers.update({'Authorization': f'Bearer {token}'})
        amount, history_id, nonce, signature = claim_all(session)
        if not amount:
            log.info(f'【{index}】领取: 暂无可领取积分')
            return False
        tx_hash, block_number = send_claim(address, private_key, amount, nonce, signature)
        log.info(f'【{index}】领取交易Hash: {tx_hash}   区块高度: {block_number}')
        time.sleep(3)
        result = claim(session, history_id, tx_hash)
        log.info(f'【{index}】{result}')
        time.sleep(2)


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
