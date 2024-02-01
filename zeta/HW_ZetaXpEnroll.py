"""
cron: 1 1 1 1 1
new Env('Zeta_XP注册')
"""
import base64
import time
from urllib.parse import parse_qs

from eth_typing import ChecksumAddress
from tls_client import Session
from web3 import Web3, HTTPProvider
from web3.exceptions import ContractLogicError

from common.task import QLTask
from common.util import log, get_env, get_chrome_session, get_error_msg

TASK_NAME = 'Zeta_XP注册'
FILE_NAME = 'ZetaWallet.txt'

RPC_NAME = 'Zeta_RPC'
rpc = get_env(RPC_NAME)
if rpc is None or rpc == '':
    rpc = "https://zetachain-evm.blockpi.network/v1/rpc/public"
    log.info(f"暂未设置RPC，默认RPC: {rpc}")

zeta = Web3(HTTPProvider(rpc))

abi = [{"inputs": [{"internalType": "address", "name": "inviter", "type": "address"},
                   {"internalType": "uint256", "name": "expiration", "type": "uint256"},
                   {"components": [{"internalType": "uint8", "name": "v", "type": "uint8"},
                                   {"internalType": "bytes32", "name": "r", "type": "bytes32"},
                                   {"internalType": "bytes32", "name": "s", "type": "bytes32"}],
                    "internalType": "struct InvitationManager.Signature", "name": "signature", "type": "tuple"}],
        "name": "confirmAndAcceptInvitation", "outputs": [], "type": "function"}]

contract_address = zeta.to_checksum_address('0x3C85e0cA1001F085A3e58d55A0D76E2E8B0A33f9')
contract = zeta.eth.contract(address=contract_address, abi=abi)

invite_code = 'YWRkcmVzcz0weDgwQjhCZURCYjI1N2UxMjQ4MDljYUI2MzdmZUY0MDc3RTAyNDYzMTEmZXhwaXJhdGlvbj0xNzA2OTg4NTg4JnI9MHgyMDJhY2E3OTM4MjNjYmRkY2E3YTMzM2MwYzQ5YzI0NzgxNmYxNDVhNjc0OTI1OTQxNmRhMTBkMzU3ZGJiODAxJnM9MHgxOWVmOGZlOTE5YjMxY2ZkNGJjMjJlMDM4OWJjOTBmZDQxNWNiMDBjMDRkZmVjYTk2YjQ4OTNmOWFkMzYxOTZkJnY9Mjg='


def send_enroll(address: ChecksumAddress, private_key: str) -> str:
    nonce = zeta.eth.get_transaction_count(address)
    parsed_dict = parse_qs(base64.b64decode(invite_code).decode())
    method = contract.functions.confirmAndAcceptInvitation(zeta.to_checksum_address(parsed_dict.get('address')[0]),
                                                           int(parsed_dict.get('expiration')[0]),
                                                           (int(parsed_dict.get('v')[0]), parsed_dict.get('r')[0],
                                                            parsed_dict.get('s')[0]))
    try:
        tx = method.build_transaction({'from': address, 'gasPrice': zeta.eth.gas_price, 'nonce': nonce})
    except ContractLogicError as e:
        return str(e)
    # gas_price = zeta.eth.gas_price
    # tx = {'from': address, 'to': contract_address, 'data': '0x90c08473', 'nonce': nonce, 'maxFeePerGas': int(gas_price * 1.2),
    #       'maxPriorityFeePerGas': int(gas_price * 1.1), 'chainId': zeta.eth.chain_id}
    # try:
    #     tx['gas'] = zeta.eth.estimate_gas(tx)
    # except ContractLogicError as e:
    #     return str(e)
    signed_tx = zeta.eth.account.sign_transaction(tx, private_key)
    transaction = zeta.eth.send_raw_transaction(signed_tx.rawTransaction)
    zeta.eth.wait_for_transaction_receipt(transaction)
    return transaction.hex()


def claim_xp(session: Session, address: ChecksumAddress, private_key: str) -> str:
    name = '注册验证'
    res = session.post('https://xp.cl04.zetachain.com/v1/enroll-in-zeta-xp', json={"address": address})
    if res.text.count('isUserVerified') and res.json().get('isUserVerified'):
        name = '领取注册XP'
        signature = zeta.eth.account.sign_typed_data(private_key, {'name': "Hub/XP", 'version': "1", 'chainId': '7000'},
                                                     {'Message': [{'name': "content", 'type': "string"}]}, {'content': "Claim XP"})
        payload = {"address": address, "task": "WALLET_VERIFY", "signedMessage": signature.signature.hex()}
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

        result = send_enroll(address, private_key)
        if result.startswith('0x'):
            log.info(f'【{index}】注册交易Hash: {result}   10S后进行注册')
            time.sleep(10)
        else:
            log.info(f'【{index}】注册交易失败: {result}')
        result = claim_xp(session, address, private_key)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
