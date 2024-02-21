"""
cron: 0 0 * * *
new Env('Star_练习游戏')
"""
import random

import requests
from tls_client import Session

from common.task import QLTask
from common.util import log
from HW_StarLogin import get_error, encrypt, get_headers
from HW_StarMining import FILE_NAME

TASK_NAME = 'Star_练习游戏'


def practice(session: Session, game: str, score: str) -> str:
    name = '练习游戏'
    payload = encrypt({"game": game, "mode": "practice", "score": score, "extra": False}, True)
    res = session.post('https://api.starnetwork.io/v3/game/record', json=payload)
    if res.text.count('id'):
        result = '获得奖励' if res.text.count('REWARDED') else '未获得奖励'
        return f'{name}[{game}]: {result}'
    return get_error(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        games = ['ballz', 'block_puzzle', 'brain_workout', 'puzzle_2048', 'sudoku', 'flappy']
        for game in games:
            if game == 'flappy':
                score = str(random.randint(100, 200))
            elif game == 'puzzle_2048':
                score = str(random.randint(12345, 23333))
            else:
                score = str(random.randint(8888, 10000))
            result = practice(session, game, score)
            log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
