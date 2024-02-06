"""
cron: 0 10 * * *
new Env('Web3Go_签到')
"""
import json
from datetime import datetime

import requests
from eth_account.messages import encode_defunct
from eth_typing import ChecksumAddress
from tls_client import Session

from common.task import QLTask
from common.util import log, get_error_msg, get_chrome_session
from HW_Web3GoMint import bsc

TASK_NAME = 'Web3Go_签到'
FILE_NAME = 'Web3GoWallet.txt'


def login(session: Session, address: ChecksumAddress, private_key: str) -> str:
    name = '获取nonce'
    res = requests.post('https://reiki.web3go.xyz/api/account/web3/web3_nonce', json={'address': address})
    if res.text.count('nonce'):
        name = '登录'
        nonce = res.json().get('nonce')
        challenge = f'reiki.web3go.xyz wants you to sign in with your Ethereum account:\n{address}\n\nWelcome to Web3Go! Click to sign in and accept the Web3Go Terms of Service. This request will not trigger any blockchain transaction or cost any gas fees. Your authentication status will reset after 7 days. Wallet address: {address} Nonce: {nonce}\n\nURI: https://reiki.web3go.xyz\nVersion: 1\nChain ID: 56\nNonce: {address}\nIssued At: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"}'
        message = encode_defunct(text=challenge)
        signature = bsc.eth.account.sign_message(message, private_key=private_key).signature.hex()
        payload = {'address': address, 'nonce': nonce, 'challenge': json.dumps({'msg': challenge}), 'signature': signature}
        res = session.post('https://reiki.web3go.xyz/api/account/web3/web3_challenge', json=payload)
        if res.text.count('token'):
            return res.json().get('extra').get('token')
    return get_error_msg(name, res)


def check_in(session: Session) -> str:
    name = '签到'
    date = datetime.now().strftime("%Y-%m-%d")
    res = session.put(f'https://reiki.web3go.xyz/api/checkin?day={date}')
    if res.text == 'true':
        return f'{name}: 成功'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        address = bsc.to_checksum_address(split[0])
        private_key = split[1]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }
        # session = get_chrome_session()
        session = requests.Session()
        session.headers.update(headers)
        session.proxies = {'https': proxy}
        token = login(session, address, private_key)
        log.info(f'【{index}】登录成功')
        session.headers.update({'Authorization': 'Bearer ' + token})
        result = check_in(session)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
