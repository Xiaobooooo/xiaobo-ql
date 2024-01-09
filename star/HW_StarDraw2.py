"""
cron: 0 1-23/3 * * *
new Env('Star_令牌抽奖')
"""
import requests
from tls_client import Session

from common.task import QLTask
from common.util import log, get_android_session
from HW_StarLogin import get_error, encrypt, get_headers
from HW_StarMining import FILE_NAME

TASK_NAME = 'Star_令牌抽奖'


def draw(session: Session) -> str:
    name = '令牌抽奖'
    res = session.get('https://api.starnetwork.io/v3/libra/draw')
    if res.text.count('EMPTY'):
        return f'{name}: EMPTY'
    if res.text.count('SUCCESS'):
        return f'{name}: 令牌'
    return get_error(name, res, completed_or_waits=['NOT_YET_FINISH'])


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        uid = split[-2]
        token = split[-1]

        session = requests.Session()
        # session = get_android_session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        result = draw(session)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
