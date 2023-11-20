"""
cron: 0 0 * * *
new Env('Star_其他游戏')
"""
import random

from common.task import QLTask
from common.util import log, get_android_session
from HW_StarFlappy import game_record
from HW_StarFlappy import FILE_NAME
from HW_StarLogin import get_headers

TASK_NAME = 'Star_其他游戏'


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        game = split[-2]
        token = split[-1]

        games = ['ballz', 'block_puzzle', 'brain_workout', 'puzzle_2048', 'sudoku']

        if not games.count(game):
            log.info(f'【{index}】不完成此任务')
            return

        # session = requests.Session()
        session = get_android_session()
        session.headers.update(get_headers(token))
        session.proxies = proxy

        score = random.randint(2333, 9999)
        result = game_record(session, game, score)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
