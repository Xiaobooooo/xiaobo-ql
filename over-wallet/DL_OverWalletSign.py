"""
cron: 33 5 * * *
new Env('OverWallet_签到')
"""
import requests
from requests import Session

from common.task import QLTask
from common.util import log, lock, get_error_msg

TASK_NAME = 'OverWallet_签到'
FILE_NAME = 'OverWalletToken.txt'


def sign(session: Session) -> str:
    name = '签到'
    res = session.post('https://mover-api-prod.over.network/daily/claim')
    if res.text.count('reward'):
        reward = res.json()['data']['reward']
        return f'{name}成功: {reward}'
    if res.text.count('code') and res.json()['code'] == -14:
        return f'{name}时间未到'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        headers = {
            'client-version': '1.0.6.53',
            'User-Agent': 'okhttp/4.9.2',
            'authorization': f'Bearer {token}',
        }
        session = requests.session()
        session.headers.update(headers)
        session.proxies = {'https': proxy}

        result = sign(session)
        log.info(f'【{index}】{result}')
        if result.count('时间未到'):
            with lock:
                self.wait += 1


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
