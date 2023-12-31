"""
cron: 30 1-23/5 * * *
new Env('Bee_挖矿')
"""
import json

import requests
from tls_client import Session

from common.task import QLTask
from common.util import log, get_error_msg, CompletedOrWaitingException

TASK_NAME = "Bee_挖矿"
FILE_NAME = "BeeToken.txt"

CLIENT_INFO = {"l": "zh_Hans", "s": "default", "os": "android", "a": "Bee Network", "p": "games.bee.app", "v": "1.20.1",
               "b": "2238"}


def mining(session: Session) -> str:
    name = '挖矿'
    url = 'https://api.bee9527.com/v2/user/mine'
    res = session.post(url, params={'clientInfo': CLIENT_INFO}, json={'clientInfo': json.dumps(CLIENT_INFO)})
    if res.text.count('balance'):
        if res.json().get('data').get('new'):
            return f'{name}: 成功'
        raise CompletedOrWaitingException(name)
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        headers = {
            'cf-country': 'HK',
            'build-number': '2238',
            'Authorization': f'Bearer {token}',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; HD1910 Build/PQ3B.190801.002)'
        }
        session = requests.session()
        session.headers.update(headers)
        session.proxies = proxy

        result = mining(session)
        log.info(f"【{index}】{result}")


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
