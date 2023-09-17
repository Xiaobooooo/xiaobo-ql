"""
cron: 0 1/2 * * *
new Env('Star_抽奖')
"""
import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock
from HW_StarLogin import get_error, encrypt_hash

TASK_NAME = 'Star_挖矿'
FILE_NAME = 'StarNetworkToken.txt'


def draw(session: Session, uid: str) -> str:
    payload = encrypt_hash({"id": uid, "action": "draw_boost"})
    res = session.post('https://api.starnetwork.io/v3/event/draw', json=payload)
    log.info(res)
    if res.text.count('drawResult'):
        result = res.json()['drawResult']
        return f'抽奖成功: {result}'
    if res.text.count('NOT_YET_FINISH'):
        return f'抽奖时间未到'
    get_error(res.text)
    msg = res.json()['message'] if res.text.count('message') else res.text
    raise Exception(f'抽奖失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        uid = split[len(split) - 2]
        token = split[len(split) - 1]
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
                result = draw(session, uid)
                if result.count('时间未到'):
                    with lock:
                        self.wait += 1
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
