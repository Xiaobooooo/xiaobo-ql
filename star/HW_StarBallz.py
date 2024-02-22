"""
cron: 45 59 21 * * *
new Env('Star_Ballz')
"""
import random

import requests
from requests import Session

from common.task import QLTask
from common.util import log, get_env
from HW_StarFlappy import FILE_NAME
from HW_StarLogin import get_headers, encrypt, get_error

TASK_NAME = 'Star_Ballz'


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
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        game = split[-2]
        token = split[-1]

        if 'ballz' != game:
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
