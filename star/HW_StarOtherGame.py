"""
cron: 0 0 * * *
new Env('Star_其他游戏')
"""
import random

import requests
from requests import Session

from common.task import QLTask
from common.util import log
from HW_StarFlappy import FILE_NAME
from HW_StarLogin import get_headers, encrypt, get_error

TASK_NAME = 'Star_其他游戏'


def game_record(session: Session, game: str, score: int) -> str:
    name = '完成游戏'
    payload = encrypt({"game": game, "mode": "tournament", "score": score, "extra": False}, True)
    res = session.post('https://api.starnetwork.io/v2/game/record', json=payload, timeout=300)
    if res.text.count('id') and res.text.count('SAVED'):
        return f'{name}: 成功'
    if res.text.count('Service Unavailable'):
        return res.text
    return get_error(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        game = split[-2]
        token = split[-1]

        games = ['ballz', 'block_puzzle', 'brain_workout', 'puzzle_2048', 'sudoku']

        if not games.count(game):
            log.info(f'【{index}】不完成此任务')
            return

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        score = random.randint(66666, 99999)
        result = game_record(session, game, score)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
