"""
cron: 0 0 * * *
new Env('Star_其他游戏')
"""
import random

import requests

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock
from HW_StarFlappy import game_record

TASK_NAME = 'Star_其他游戏'
FILE_NAME = 'StarNetworkGameToken.txt'


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name)
        self.ignore = 0

    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        game = split[len(split) - 2]
        token = split[len(split) - 1]

        games = ['ballz', 'block_puzzle', 'brain_workout', 'puzzle_2048', 'sudoku']

        if game == 'flappy':
            log.info(f'【{index}】{username}----不完成此任务')
            with lock:
                self.ignore += 1
            return True
        if not games.count(game):
            log.info(f'【{index}】{username}----游戏名有误')
            self.fail_data.append(
                f'【{index}】{username}----游戏名有误，请设置ballz、block_puzzle、brain_workout、puzzle_2048、sudoku之一')
            return False

        # delay = random.randint(1, 300)
        # log.info(f"【{index}】{username}----随机延迟{delay}秒后开始")
        # time.sleep(delay)
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
                # if game == 'puzzle_2048':
                #     score = str(random.randint(88888, 99999))
                # else:
                score = str(random.randint(88888, 99999))
                result = game_record(session, game, score)
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

    def push_data(self):
        return f'总任务数：{self.total}\n成功数：{self.success} (其中跳过数：{self.ignore})\n失败数：{len(self.fail_data)}'


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
