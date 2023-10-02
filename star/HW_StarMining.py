"""
cron: 0 0-23/2 * * *
new Env('Star_挖矿')
"""
import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock
from HW_StarLogin import get_error

TASK_NAME = 'Star_挖矿'
FILE_NAME = 'StarNetworkToken.txt'


def mining(session: Session) -> str:
    res = session.post('https://apis.starnetwork.io/v3/session/start')
    if res.text.count('NEW_SESSION_STARTED'):
        return '挖矿成功'
    if res.text.count('endAt'):
        return '挖矿时间未到'
    get_error(res.text)
    msg = res.json()['message'] if res.text.count('message') else res.text
    raise Exception(f'挖矿失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[-1]
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
                result = mining(session)
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
                    proxy = get_proxy(self.api_url)
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
