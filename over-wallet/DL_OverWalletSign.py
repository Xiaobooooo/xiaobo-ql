"""
cron: 33 5 * * *
new Env('OverWallet_签到')
"""
import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = 'OverWallet_签到'
FILE_NAME = 'OverWalletToken.txt'


def sign(session: Session) -> str:
    res = session.post('https://mover-api-prod.over.network/daily/claim')
    if res.text.count('reward'):
        reward = res.json()['data']['reward']
        return f'签到成功: {reward}'
    if res.text.count('code') and res.json()['code'] == -14:
        return '签到时间未到'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'签到失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[-1]
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {
            'client-version': '1.0.6.53',
            'User-Agent': 'okhttp/4.9.2',
            'authorization': f'Bearer {token}',
        }

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                result = sign(session)
                if result.count('时间未到'):
                    with lock:
                        self.wait += 1
                log.info(f'【{index}】{username}----{result}')
                return True
            except:
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
