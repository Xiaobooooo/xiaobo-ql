"""
cron: 30 1-23/5 * * *
new Env('Bee_挖矿')
"""
import json

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = "Bee_挖矿"
FILE_NAME = "BeeToken.txt"

CLIENT_INFO = {"l": "zh_Hans", "s": "default", "os": "android", "a": "Bee.com", "p": "games.bee.app", "v": "1.7.7.1482",
               "b": "1482"}


def get_headers(token=None):
    headers = {"cf-country": "HK", "build-number": "1482"}
    if token is not None and token != '':
        headers['Authorization'] = "Bearer {}".format(token)
    return headers


def mining(session: Session) -> str:
    res = session.post('https://api.bee9527.com/v2/user/mine', params={'clientInfo': CLIENT_INFO},
                       json={'clientInfo': json.dumps(CLIENT_INFO)})
    if res.text.count('balance') == 0:
        msg = res.json()['msg'] if res.text.count('msg') else res.text
        raise Exception(f'挖矿失败:{msg}')
    else:
        if res.json()['data']['new']:
            return '挖矿成功'
        else:
            return '挖矿时间未到'


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[len(split) - 1]
        log.info(f"【{index}】{username}----正在完成任务")

        session = requests.session()
        session.headers = {
            'cf-country': 'HK',
            'build-number': '1482',
            'Authorization': f'Bearer {token}',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; HD1910 Build/PQ3B.190801.002)'
        }

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {"https": proxy}
            try:
                result = mining(session)
                if result == '挖矿时间未到':
                    with lock:
                        self.wait += 1
                log.info(f"【{index}】{username}----{result}")
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
