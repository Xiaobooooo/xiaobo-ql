"""
cron: 0 0-23/2 * * *
new Env('Star_挖矿')
"""
import requests
from tls_client import Session

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_error, get_headers

TASK_NAME = 'Star_挖矿'
FILE_NAME = 'StarNetworkToken.txt'


def mining(session: Session) -> str:
    name = '挖矿'
    res = session.post('https://apis.starnetwork.io/v3/session/start')
    if res.text.count('NEW_SESSION_STARTED'):
        return f'{name}: 成功'
    return get_error(name, res, completed_or_waits=['endAt'])


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        result = mining(session)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
