"""
cron: 0 0 * * *
new Env('Star_练习游戏')
"""
import random
import time

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc
from HW_StarLogin import get_error, encrypt

TASK_NAME = 'Star_练习游戏'
FILE_NAME = 'StarNetworkToken.txt'


def practice(session: Session, game: str, score: str) -> str:
    payload = encrypt({"game": game, "mode": "practice", "score": score, "extra": False}, True)
    res = session.post('https://api.starnetwork.io/v3/game/record', json=payload)
    if res.text.count('id'):
        result = '获得奖励' if res.text.count('REWARDED') else '未获得奖励'
        return f'【{game}】练习成功: {result}'
    get_error(res.text)
    msg = res.json()['message'] if res.text.count('message') else res.text
    raise Exception(f'练习失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[len(split) - 1]

        delay = random.randint(1, 300)
        log.info(f"【{index}】{username}----随机延迟{delay}秒后开始")
        time.sleep(delay)
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {
            'User-Agent': 'Dart/2.19 (dart:io)',
            'Authorization': f'Bearer {token}'
        }

        proxy = get_proxy(self.api_url)

        games = ['ballz', 'block_puzzle', 'brain_workout', 'puzzle_2048', 'sudoku', 'flappy']
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                for game in games:
                    if game == 'flappy':
                        score = str(random.randint(100, 200))
                    elif game == 'puzzle_2048':
                        score = str(random.randint(12345, 23333))
                    else:
                        score = str(random.randint(8888, 10000))
                    result = practice(session, game, score)
                    log.info(f'【{index}】{username}----{result}')
                return True
            except:
                if log_exc().count('账号被封禁或登录失效'):
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
                    return False
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
