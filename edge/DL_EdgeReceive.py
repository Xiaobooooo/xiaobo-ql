"""
cron: 11 10 * * *
new Env('Edge_领取')
"""
import hashlib
import time

from tls_client import Session

from common.task import QLTask
from common.util import log, get_error_msg, get_android_session

TASK_NAME = 'Edge_领取'
FILE_NAME = 'EdgeToken'


def get_token(session: Session, uid: str) -> str:
    data = "uid=" + uid
    res = session.post('https://edge.edgesmartchain.com/index/index/get_token', data=data)
    if res.text.count('access_token'):
        return res.json().get('access_token')
    return get_error_msg('获取Token', res)


def lq(session: Session, uid: str, token: str) -> str:
    name = '领取'
    timestamp = str(int(time.time()))
    sign = hashlib.md5(("edgesj" + token + timestamp + uid).encode()).hexdigest()
    data = "uid=" + uid + "&access_token=" + token + "&sign=" + sign + "&times=" + timestamp
    res = session.post('https://edge.edgesmartchain.com/index/index/lq_post', data=data)
    if res.text.count('today_post'):
        return f'{name}: {res.json().get("today_post")} POST'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        uid = split[-2]

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Linux; Android 9; LIO-AN00 Build/PQ3B.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 uni-app Html5Plus/1.0 (Immersed/24.0)'
        }
        session = get_android_session()
        session.headers.update(headers)
        session.proxies = proxy

        token1 = get_token(session, uid)
        log.info(f'【{index}】获取Token: 成功')
        result = lq(session, uid, token1)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
