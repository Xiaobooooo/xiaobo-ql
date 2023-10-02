"""
cron: 30 2-23/5 * * *
new Env('Eagle_挖矿')
"""
import time

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = "Eagle_挖矿"
FILE_NAME = "EagleToken.txt"


def mining(session: Session) -> str:
    res = session.post("https://eaglenetwork.app/api/start-mining", json={})
    if res.text.count('start_time') > 0:
        return '挖矿成功'
    if res.text.count('Mining Already Started') > 0:
        return '挖矿时间未到'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'挖矿失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[-1]
        log.info(f"【{index}】{username}----正在完成任务")

        session = requests.session()
        session.headers = {
            'UserAgent': 'android 1.0.65',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; HD1910 Build/PQ3B.190801.002)',
            'AuthToken': token
        }

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {"https": proxy}
            try:
                result = mining(session)
                if result.count('时间未到'):
                    with lock:
                        self.wait += 1
                log.info(f"【{index}】{username}----{result}----延迟1S后结束")
                time.sleep(1)
                return True
            except:
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                    proxy = get_proxy(self.api_url)
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
