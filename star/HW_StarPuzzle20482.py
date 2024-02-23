"""
cron: 15 1 * * *
new Env('Star_Puzzle2048_小号')
"""
import requests

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_headers
from HW_StarFlappy import game_record
from HW_StarBallz2 import FILE_NAME

TASK_NAME = 'Star_Puzzle2048_小号'


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        for i in range(30):
            result = game_record(session, 'puzzle_2048', 0)
            log.info(f'【{index}】{result}')
            if result.count('失败'):
                break


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
