"""
cron: 0 10 * * *
new Env('Ulti-Pilot_Explore')
"""
import time

from eth_account.messages import encode_defunct
from eth_typing import ChecksumAddress
from tls_client import Session
from web3 import Web3, HTTPProvider

from common.task import QLTask
from common.util import log, get_chrome_session, get_error_msg

TASK_NAME = 'Ulti-Pilot_Explore'
FILE_NAME = 'UltiPilotAddress.txt'

bsc = Web3(HTTPProvider("https://opbnb-mainnet-rpc.bnbchain.org"))
chain_id = bsc.eth.chain_id


def login(session: Session, address: ChecksumAddress, private_key: str) -> str:
    name = '登录-获取签名'
    payload = {"address": address, "feature": "assets-wallet-login", "chainId": 204}
    res = session.post('https://toolkit.ultiverse.io/api/user/signature', json=payload)
    if res.text.count('message'):
        msg = res.json().get('data').get('message')
        message = encode_defunct(text=msg)
        signature = bsc.eth.account.sign_message(message, private_key=private_key).signature.hex()
        name = '登录'
        payload = {"address": address, "signature": signature, "chainId": 204}
        res = session.post('https://toolkit.ultiverse.io/api/wallets/signin', json=payload)
        if res.text.count('access_token'):
            return res.json().get('data').get('access_token')
    return get_error_msg(name, res)


def query(session: Session) -> list:
    name = '查询'
    res = session.get('https://pml.ultiverse.io/api/explore/list')
    world_ids = []
    if res.text.count('success') and res.json().get('success'):
        for data in res.json().get('data'):
            if not data.get('explored'):
                world_ids.append(data.get('worldId'))
        return world_ids
    get_error_msg(name, res)


def explore(session: Session, world_ids: list, address: ChecksumAddress, private_key: str) -> (str, list, int):
    name = '浏览'
    while True:
        payload = {"worldIds": world_ids, "chainId": 204}
        res = session.post('https://pml.ultiverse.io/api/explore/sign', json=payload)
        if res.text.count('Insufficient soul point'):
            world_ids.pop()
            time.sleep(10)
        elif res.text.count('Request too frequent'):
            time.sleep(10)
        elif res.text.count('Already explored for Terminus'):
            return f'{name}: 今日已经浏览过了', -1
        else:
            break
    if res.text.count('deadline'):
        data_json = res.json().get('data')
        contract = data_json.get('contract')
        deadline = data_json.get('deadline')
        voyage_id = data_json.get('voyageId')
        destinations = data_json.get('destinations')
        data = data_json.get('data')
        signature = data_json.get('signature')
        nonce = bsc.eth.get_transaction_count(address)
        destinations_hex = hex(224 + (len(destinations) - 1) * 32).replace("0x", "")
        for i in range(64 - len(destinations_hex)):
            destinations_hex = f'0{destinations_hex}'
        data = f'0x75278b5c00000000000000000000000000000000000000000000000000000000{hex(deadline).replace("0x", "")}0000000000000000000000000000000000000000000000000000000000{hex(voyage_id).replace("0x", "")}00000000000000000000000000000000000000000000000000000000000000a0{data.replace("0x", "")}{destinations_hex}000000000000000000000000000000000000000000000000000000000000000{len(destinations)}{"".join([f"000000000000000000000000000000000000000000000000000000000000000{i}" for i in destinations])}0000000000000000000000000000000000000000000000000000000000000041{signature.replace("0x", "")}00000000000000000000000000000000000000000000000000000000000000'
        tx = {'from': address, 'to': contract, 'nonce': nonce, 'data': data, 'gasPrice': bsc.eth.gas_price, 'gas': 100000}
        bsc.eth.estimate_gas(tx)
        signed_tx = bsc.eth.account.sign_transaction(tx, private_key)
        transaction = bsc.eth.send_raw_transaction(signed_tx.rawTransaction)
        bsc.eth.wait_for_transaction_receipt(transaction)
        return transaction.hex(), world_ids, voyage_id
    return get_error_msg(name, res)


def check(session: Session, voyage_id: int) -> str:
    name = '检测浏览'
    res = session.get(f'https://pml.ultiverse.io/api/explore/check?id={voyage_id}&chainId=204')
    if res.text.count('success'):
        return f"{name}: {'成功' if res.json().get('data').get('success') else '失败'}"
    return get_error_msg(name, res)


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str, is_delay: bool):
        super().__init__(task_name, file_name, is_delay)
        self.voyage_id_list = []
        self.world_ids_list = []
        for i in range(self.total):
            self.world_ids_list.append([])
            self.voyage_id_list.append(0)

    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        address = bsc.to_checksum_address(split[0])
        private_key = split[1]

        headers = {
            'ul-auth-api-key': 'YWktYWdlbnRAZFd4MGFYWmxjbk5s',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Origin': 'https://pilot.ultiverse.io'
        }
        session = get_chrome_session()
        session.headers.update(headers)
        session.proxies = proxy

        token = login(session, address, private_key)
        session.headers.update({'ul-auth-address': address, 'ul-auth-token': token})
        log.info(f'【{index}】登录成功')

        if not self.world_ids_list[index - 1]:
            world_ids = query(session)
            self.world_ids_list[index - 1] = world_ids
        if not self.voyage_id_list[index - 1]:
            result, world_ids, voyage_id = explore(session, self.world_ids_list[index - 1], address, private_key)
            if voyage_id == -1:
                log.info(f'【{index}】{result}')
                return
            self.voyage_id_list[index - 1] = voyage_id
            log.info(f'【{index}】{world_ids}浏览交易Hash: {result}')
        result = check(session, self.voyage_id_list[index - 1])
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, False).run()
