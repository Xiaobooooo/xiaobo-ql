"""
cron: 0 1-23/3 * * *
new Env('Star_签到')
"""
import requests
from tls_client import Session

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_error, get_headers
from HW_StarMining import FILE_NAME

TASK_NAME = 'Star_签到'


def check_in(session: Session) -> str:
    name = '签到'
    res = session.post('https://api.starnetwork.io/v3/user/checkin')
    if res.text.count('CLAIMED'):
        return f'{name}: 成功'
    return get_error(name, res, completed_or_waits=['NotFoundError'])


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        result = check_in(session)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
