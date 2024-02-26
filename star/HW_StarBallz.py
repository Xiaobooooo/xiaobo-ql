"""
cron: 30 59 21 * * *
new Env('Star_Ballz')
"""
import random

import requests
from requests import Session

from common.task import QLTask
from common.util import log, lock
from HW_StarFlappy import FILE_NAME
from HW_StarLogin import get_headers, encrypt, get_error

TASK_NAME = 'Star_Ballz'


def query_score(session: Session, game: str) -> int:
    name = '查询分数'
    res = session.get(f'https://api.starnetwork.io/v3/game/{game}', timeout=300)
    if res.text.count('tournament'):
        if not res.json().get('tournament'):
            return 23333
        tournament_id = ''
        ids = res.json()['tournament']['_id']['id']['data']
        for data in ids:
            val = str(hex(data)[2:])
            if len(val) == 1:
                val = '0' + str(hex(data)[2:])
            tournament_id = tournament_id + val
        res = session.get(f'https://api.starnetwork.io/v3/game/leaderboard/{tournament_id}', timeout=300)
        if res.text.count('top'):
            tops = res.json().get('data').get('top')
            for top in tops:
                score_str = top.get('score')
                try:
                    return int(score_str)
                except:
                    continue
        return 23333
    return get_error(name, res)


def game_record(session: Session, game: str, score: int) -> str:
    name = '完成游戏'
    payload = encrypt({"game": game, "mode": "tournament", "score": score, "extra": False}, True)
    res = session.post('https://api.starnetwork.io/v2/game/record', json=payload, timeout=300)
    if res.text.count('id') and res.text.count('SAVED'):
        return f'{name}[{game}]: 成功'
    if res.text.count('SAVED') or res.text.count('FAILED'):
        return f'{name}[{game}]: 失败'
    if res.text.count('Service Unavailable'):
        return res.text
    return get_error(name, res)


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str, game: str):
        super().__init__(task_name, file_name)
        self.game = game
        self.score = None

    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        game = split[-2]
        token = split[-1]

        if self.game != game:
            log.info(f'【{index}】不完成此任务')
            return

        session = requests.Session()
        session.headers.update(get_headers(token))
        session.proxies = {'https': proxy}

        with lock:
            if not self.score:
                self.score = query_score(session, self.game)
                log.info(f'[{self.game}]当前第一名分数: {self.score}')

        score = self.score + random.randint(23333, 66666)
        if score >= 730000:
            score = 723333
        log.info(f'【{index}】随机分数: {score}')

        result = game_record(session, self.game, score)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'ballz').run()
