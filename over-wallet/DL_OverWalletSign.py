"""
cron: 33 6 * * *
new Env('OverWallet_签到')
"""
from tls_client import Session

from common.task import QLTask
from common.util import log, get_error_msg, get_android_session, CompletedOrWaitingException

TASK_NAME = 'OverWallet_签到'
FILE_NAME = 'OverWalletToken.txt'


def get_headers(token: str) -> dict:
    return {'client-version': '1.0.6.74', 'User-Agent': 'okhttp/4.9.2', 'authorization': f'Bearer {token}'}


def sign(session: Session) -> str:
    name = '签到'
    res = session.post('https://mover-api-prod.over.network/daily/claim')
    if res.text.count('reward'):
        reward = res.json().get('data').get('reward')
        return f'{name}: {reward} Point'
    if res.text.count('code') and res.json()['code'] == -14:
        raise CompletedOrWaitingException(name)
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = get_android_session()
        session.headers.update(get_headers(token))
        session.proxies = proxy

        result = sign(session)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
