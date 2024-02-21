"""
cron: 30 0 1-23/8 * * *
new Env('Star_加速抽奖_小号')
"""
import requests
from requests import Session

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_headers, get_error
from HW_StarDrawSpeed import draw

TASK_NAME = 'Star_加速抽奖_小号'
FILE_NAME = 'StarNetworkToken2.txt'


def get_uid(session: Session):
    name = '获取ID'
    res = session.get('https://api.starnetwork.io/v3/auth/user')
    if res.text.count('{"id":'):
        return res.json()['id']
    return get_error(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        uid = get_uid(session)
        log.info(f'【{index}】UID获取成功')
        result = draw(session, uid)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
