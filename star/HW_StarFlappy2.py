"""
cron: 0 7 * * *
new Env('Star_Flappy_小号')
"""
import time

import requests

from common.task import QLTask, get_proxy
from common.util import log
from HW_StarLogin import get_headers
from HW_StarFlappy import game_record

TASK_NAME = 'Star_Flappy_小号'
FILE_NAME = 'StarNetworkFlappyToken.txt'


class Task(QLTask):

    def __init__(self, task_name: str, file_name: str, game: str):
        super().__init__(task_name, file_name)
        self.thread_num = 30
        self.game = game
        self.star_time = time.time()

    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        i = 0
        while True:
            if time.time() - self.star_time > 3600:
                break
            result = game_record(session, self.game, 0)
            log.info(f'【{index}】{result}')
            if result.count('失败'):
                break
            i += 1
            if i > 5:
                i = 0
                proxy = get_proxy(self.api_url, index)
                session.proxies = {'https': proxy}


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'flappy').run()
