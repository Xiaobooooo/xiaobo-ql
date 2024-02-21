"""
cron: 15 21 * * *
new Env('Star_Ballz_小号')
"""
import random

import requests

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_headers
from HW_StarFlappy import game_record

TASK_NAME = 'Star_Ballz_小号'
FILE_NAME = 'StarNetworkBallzToken.txt'


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        score = random.randint(6666, 9999)

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        result = game_record(session, 'ballz', score)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
