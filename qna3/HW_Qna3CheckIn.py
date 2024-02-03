"""
cron: 0 10 * * *
new Env('Qna3_签到')
"""
import sys
import time

from eth_account.messages import encode_defunct
from eth_typing import ChecksumAddress
from tls_client import Session
from web3 import Web3, HTTPProvider

from common.task import QLTask
from common.util import log, get_chrome_session, get_error_msg, get_env

TASK_NAME = 'Qna3_签到'
FILE_NAME = 'Qna3Wallet.txt'

INVITE_CODE_NAME = 'QNA3_INVITE_CODE'
invite_code = get_env(INVITE_CODE_NAME)
if invite_code is None or invite_code == '':
    log.info("暂未设置邀请码INVITE_CODE")

RPC_NAME = 'QNA3_RPC'
rpc = get_env(RPC_NAME)
if rpc is None or rpc == '':
    # rpc = "https://bsc-dataseed2.defibit.io"
    rpc = "https://opbnb-mainnet-rpc.bnbchain.org"
    log.info(f"暂未设置RPC，默认opBNB RPC: {rpc}")

bsc = Web3(HTTPProvider(rpc))
chain_id = bsc.eth.chain_id

if chain_id == 56:
    via = 'bnb'
elif chain_id == 204:
    via = 'opbnb'
else:
    log.error("链ID获取失败，请检查RPC")
    sys.exit()

contract_address = bsc.to_checksum_address('0xb342e7d33b806544609370271a8d074313b7bc30')
abi = [{"inputs": [{"name": "param_uint256_1", "type": "uint256"}], "name": "checkIn", "outputs": [], "type": "function"},
       {"inputs": [{"name": "activityIndex", "type": "uint256"}, {"name": "id", "type": "uint256"},
                   {"name": "credit", "type": "uint32"}], "name": "vote", "outputs": [], "type": "function"}]
contract = bsc.eth.contract(address=contract_address, abi=abi)


def login(session: Session, address: ChecksumAddress, private_key: str) -> str:
    name = '登录'
    msg = 'AI + DYOR = Ultimate Answer to Unlock Web3 Universe'
    message = encode_defunct(text=msg)
    signature = bsc.eth.account.sign_message(message, private_key=private_key).signature.hex()
    payload = {'wallet_address': address, 'signature': signature, "invite_code": invite_code}
    res = session.post('https://api.qna3.ai/api/v2/auth/login?via=wallet', json=payload)
    if res.text.count('accessToken'):
        return res.json().get('data').get("accessToken")
    return get_error_msg(name, res)


def query_check_in(session: Session) -> str:
    name = '查询签到'
    res = session.post('https://api.qna3.ai/api/v2/graphql', json={
        "query": "query loadUserDetail($cursored: CursoredRequestInput!) {\n  userDetail {\n    checkInStatus {\n      checkInDays\n      todayCount\n      checked\n    }\n    credit\n    creditHistories(cursored: $cursored) {\n      cursorInfo {\n        endCursor\n        hasNextPage\n      }\n      items {\n        claimed\n        extra\n        id\n        score\n        signDay\n        signInId\n        txHash\n        typ\n      }\n      total\n    }\n    invitation {\n      code\n      inviteeCount\n      leftCount\n    }\n    origin {\n      email\n      id\n      internalAddress\n      userWalletAddress\n    }\n    voteHistoryOfCurrentActivity {\n      created_at\n      query\n    }\n    ambassadorProgram {\n      bonus\n      claimed\n      family {\n        checkedInUsers\n        totalUsers\n      }\n    }\n  }\n}",
        "variables": {"cursored": {"after": "", "first": 20}}})
    if res.text.count('checkInStatus'):
        return res.json().get('data').get("userDetail").get("checkInStatus").get("checked")
    return get_error_msg(name, res)


def send_check_in(address: ChecksumAddress, private_key: str) -> str:
    nonce = bsc.eth.get_transaction_count(address)
    method = contract.functions.checkIn(1)
    tx = method.build_transaction({'gas': 33333, 'gasPrice': bsc.eth.gas_price, 'nonce': nonce})
    signed_tx = bsc.eth.account.sign_transaction(tx, private_key)
    transaction = bsc.eth.send_raw_transaction(signed_tx.rawTransaction)
    bsc.eth.wait_for_transaction_receipt(transaction)
    return transaction.hex()


def check_in(session: Session, tx_hash) -> str:
    name = '签到'
    payload = {"hash": tx_hash, "via": via}
    res = session.post('https://api.qna3.ai/api/v2/my/check-in', json=payload)
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
        result = query_check_in(session)
        if result:
            log.info(f'【{index}】签到: 今日已签到')
            return
        tx_hash = send_check_in(address, private_key)
        log.info(f'【{index}】签到交易Hash: {tx_hash}')
        time.sleep(3)
        result = check_in(session, tx_hash)
        log.info(f'【{index}】{result}')
        time.sleep(2)


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
