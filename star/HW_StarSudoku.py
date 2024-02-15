"""
cron: 45 59 1 * * *
new Env('Star_Sudoku')
"""
import random

import requests

from common.task import QLTask
from common.util import log, get_env
from HW_StarFlappy import FILE_NAME, game_record
from HW_StarLogin import get_headers

TASK_NAME = 'Star_Sudoku'


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        game = split[-2]
        token = split[-1]

        if 'sudoku' != game:
            log.info(f'【{index}】不完成此任务')
            return

        sc = get_env(game)
        if not sc:
            score = random.randint(66666, 99999)
            log.info(f'【{index}】默认随机分数: {score}')
        else:
            if sc.count('-'):
                temps = sc.split('-')
                score = random.randint(int(temps[0]), int(temps[1]))
                log.info(f'【{index}】指定随机分数: {score}')
            else:
                score = int(sc)
                log.info(f'【{index}】指定分数: {score}')

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        result = game_record(session, game, score)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
