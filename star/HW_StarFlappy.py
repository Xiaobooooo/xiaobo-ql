"""
cron: 59 7 * * *
new Env('Star_Flappy游戏')
"""
import datetime
import random
import time

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock
from HW_StarLogin import get_error, encrypt

TASK_NAME = 'Star_Flappy游戏'
FILE_NAME = 'StarNetworkGameToken.txt'


def game_record(session: Session, game: str, score: str) -> str:
    payload = encrypt({"game": game, "mode": "tournament", "score": score, "extra": False}, True)
    res = session.post('https://api.starnetwork.io/v3/game/record', json=payload)
    if res.text.count('id') and res.text.count('SAVED'):
        return '完成游戏成功'
    if res.text.count('Service Unavailable'):
        return res.text
    get_error(res.text)
    msg = res.json()['message'] if res.text.count('message') else res.text
    raise Exception(f'游戏完成失败:{msg}')


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name, False)
        self.ignore = 0

    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        game = split[-2]
        token = split[-1]
        if game != 'flappy':
            log.info(f'【{index}】{username}----不完成此任务')
            with lock:
                self.ignore += 1
            return True

        # log.info(f"【{index}】{username}----延迟55秒后开始")
        # time.sleep(55)
        delay = random.randint(10, 30)
        log.info(f"【{index}】{username}----随机延迟{delay}秒后开始")
        time.sleep(delay)
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {
            'User-Agent': 'Dart/2.19 (dart:io)',
            'Authorization': f'Bearer {token}'
        }

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                second = float(datetime.datetime.now().strftime('%S.%f'))
                if second >= 55 or second <= 10:
                    result = game_record(session, game, '200')
                    log.info(f'【{index}】{username}----{result}')
                else:
                    success = 0
                    run = 0
                    while success < 1 and run < 20:
                        run += 1
                        result = game_record(session, game, '200')
                        if result == '完成游戏成功':
                            success += 1
                        log.info(f'【{index}】{username}----{result}')
                return True
            except:
                if log_exc().count('账号被封禁或登录失效'):
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
                    return False
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                    proxy = get_proxy(self.api_url)
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False

    def push_data(self):
        return f'总任务数：{self.total}\n成功数：{self.success} (其中跳过数：{self.ignore})\n失败数：{len(self.fail_data)}'


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
