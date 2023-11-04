"""
cron: 59 7 * * *
new Env('Star_Flappy游戏')
"""
import datetime

from tls_client import Session

from common.task import QLTask
from common.util import log, get_android_session
from HW_StarLogin import get_error, encrypt, get_headers

TASK_NAME = 'Star_Flappy游戏'
FILE_NAME = 'StarNetworkGameToken.txt'


def game_record(session: Session, game: str, score: str) -> str:
    name = '完成游戏'
    payload = encrypt({"game": game, "mode": "tournament", "score": score, "extra": False}, True)
    res = session.post('https://api.starnetwork.io/v3/game/record', json=payload, timeout_seconds=300)
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
        if game != 'flappy':
            log.info(f'【{index}】不完成此任务')
            return

        # session = requests.Session()
        session = get_android_session()
        session.headers.update(get_headers(token))
        session.proxies = proxy

        second = float(datetime.datetime.now().strftime('%S.%f'))
        if second >= 55 or second <= 10:
            result = game_record(session, game, '200')
            log.info(f'【{index}】{result}')
        else:
            success = 0
            run = 0
            while success < 1 and run < 20:
                run += 1
                result = game_record(session, game, '200')
                if result == '完成游戏成功':
                    success += 1
                log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
