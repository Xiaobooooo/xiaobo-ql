"""
cron: 11 10 * * *
new Env('Edge_领取')
"""
import hashlib
import time

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = 'Edge_领取'
FILE_NAME = 'EdgeToken'


def get_token(session: Session, uid: str) -> str:
    data = "uid=" + uid
    res = session.post('https://edge.edgesmartchain.com/index/index/get_token', data=data)
    if res.text.count('access_token'):
        return res.json().get('access_token')
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'Token获取失败:{msg}')


def lq(session: Session, uid: str, token: str) -> str:
    timestamp = str(int(time.time()))
    sign = hashlib.md5(("edgesj" + token + timestamp + uid).encode()).hexdigest()
    data = "uid=" + uid + "&access_token=" + token + "&sign=" + sign + "&times=" + timestamp
    res = session.post('https://edge.edgesmartchain.com/index/index/lq_post', data=data)
    if res.text.count('today_post'):
        return f'领取成功: {res.json().get("today_post")}'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'领取失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        uid = split[-2]
        token = split[-1]

        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Linux; Android 9; HD1910 Build/PQ3B.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/24.0)'
        }

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                token1 = get_token(session, uid)
                log.info(f'【{index}】{username}----Token获取成功')
                result = lq(session, uid, token1)
                log.info(f'【{index}】{username}----{result}')
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
