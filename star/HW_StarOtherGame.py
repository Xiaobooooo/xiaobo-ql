"""
cron: 0 0 * * *
new Env('Star_其他游戏')
"""
import random

import requests

from common.task import QLTask
from common.util import log, lock
from HW_StarFlappy import game_record
from HW_StarFlappy import FILE_NAME

TASK_NAME = 'Star_其他游戏'


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name)
        self.ignore = 0

    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        game = split[-2]
        token = split[-1]

        games = ['ballz', 'block_puzzle', 'brain_workout', 'puzzle_2048', 'sudoku']

        if game == 'flappy':
            log.info(f'【{index}】不完成此任务')
            with lock:
                self.ignore += 1
            return
        if not games.count(game):
            log.info(f'【{index}】游戏名有误')
            self.fail_data.append(f'【{index}】游戏名有误')
            return

        headers = {
            'User-Agent': 'Dart/2.19 (dart:io)',
            'Authorization': f'Bearer {token}'
        }
        session = requests.session()
        session.headers.update(headers)
        session.proxies = {'https': proxy}

        score = str(random.randint(2333, 9999))
        result = game_record(session, game, score)
        log.info(f'【{index}】{result}')

    def get_push_data(self, data: str = None) -> str:
        data = f'总任务数: {self.total}\n成功数: {self.success} (其中跳过数: {self.ignore})\n失败数: {len(self.fail_data)}'
        return super().get_push_data(data)


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
