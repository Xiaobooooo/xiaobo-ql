"""
cron: 0 0-23/2 * * *
new Env('Star_挖矿')
"""
import requests
from tls_client import Session

from common.task import QLTask
from common.util import log, lock, get_android_session
from HW_StarLogin import get_error

TASK_NAME = 'Star_挖矿'
FILE_NAME = 'StarNetworkToken.txt'


def mining(session: Session) -> str:
    name = '挖矿'
    res = session.post('https://apis.starnetwork.io/v3/session/start')
    if res.text.count('NEW_SESSION_STARTED'):
        return f'{name}成功'
    if res.text.count('endAt'):
        return f'{name}时间未到'
    return get_error(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        headers = {
            'User-Agent': 'Dart/2.19 (dart:io)',
            'Authorization': f'Bearer {token}'
        }
        session = requests.Session()
        session.headers.update(headers)
        session.proxies = {'https': proxy}

        result = mining(session)
        log.info(f'【{index}】{result}')
        if result.count('时间未到'):
            with lock:
                self.wait += 1


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
