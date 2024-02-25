"""
cron: 0 7 * * *
new Env('Star_Flappy_小号')
"""
import requests

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_headers
from HW_StarFlappy import game_record

TASK_NAME = 'Star_Flappy_小号'
FILE_NAME = 'StarNetworkGameToken2.txt'


class Task(QLTask):

    def __init__(self, task_name: str, file_name: str, game: str):
        super().__init__(task_name, file_name)
        self.thread_num = 30
        self.game = game

    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        while True:
            result = game_record(session, self.game, 0)
            log.info(f'【{index}】{result}')
            if result.count('失败'):
                break


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'flappy').run()
