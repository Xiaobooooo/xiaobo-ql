"""
cron: 0 0-23/2 * * *
new Env('Star_挖矿小号')
"""
import requests

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_headers
from HW_StarMining import mining

TASK_NAME = 'Star_挖矿小号'
FILE_NAME = 'StarNetworkToken2.txt'


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        # session = get_android_session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        result = mining(session)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
