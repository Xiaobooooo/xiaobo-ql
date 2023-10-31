"""
cron: 0 1-23/3 * * *
new Env('Star_抽奖')
"""
from tls_client import Session

from common.task import QLTask
from common.util import log, lock, get_android_session
from HW_StarLogin import get_error, encrypt
from HW_StarMining import FILE_NAME

TASK_NAME = 'Star_抽奖'


def draw(session: Session, uid: str) -> str:
    name = '抽奖'
    payload = encrypt({"id": uid, "action": "draw_boost"})
    res = session.post('https://api.starnetwork.io/v3/event/draw', json=payload)
    if res.text.count('drawResult'):
        result = res.json()['drawResult']
        return f'{name}成功: {result}'
    if res.text.count('NOT_YET_FINISH'):
        return f'{name}时间未到'
    return get_error(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        uid = split[-2]
        token = split[-1]

        headers = {
            'User-Agent': 'Dart/2.19 (dart:io)',
            'Authorization': f'Bearer {token}'
        }
        session = get_android_session()
        session.headers.update(headers)
        session.proxies = {'https': proxy}

        result = draw(session, uid)
        log.info(f'【{index}】{result}')
        if result.count('时间未到'):
            with lock:
                self.wait += 1


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
