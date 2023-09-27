"""
cron: 0 8 * * *
new Env('点码广告_签到')
"""
import hashlib
import random
import time

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = '点码广告_签到'
FILE_NAME = '点码广告Token.txt'


def get_sign(data: str) -> str:
    data += 'kaed499-28b6c504-824ed2ccb4e-3ce07a'
    return hashlib.md5(data.encode()).hexdigest()


def sign(session: Session, uid: str) -> str:
    url = 'https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/yxapp/ads/addViewCount2'
    timestamp = int(time.time() * 1000)
    time_check = random.randint(156666, 233333)
    payload1 = {"timestamp": 1695821746421, "sign": "2d775f80ef9b556e2b483bc2a9e17915", "adPlatform": "1",
                "adId": "660441450537816064", "adType": "3", "adReward": "1", "type": "Android", "viewType": 1,
                "userId": uid, "taskType": 1, "videos": 1}
    payload2 = {"timestamp": 1695821906343, "sign": "646e771662dd9a05fe575d4836298f40", "adPlatform": "2",
                "adId": "12E990ADC812099AFD1C94BA2B40F18F", "adType": "3", "adReward": "1", "type": "Android", "viewType": 1,
                "userId": uid, "taskType": 1, "videos": 1, "tasks": 1}
    session.post(url, json=payload1)
    res = session.post(url, json=payload2)
    if res.text.count('isFinish') and res.json()['body']['isFinish'] == 1:
        return '签到成功'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'签到失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        uid = split[-2]
        token = split[-1]
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {
            'Version': 'wangcai-2.0.0v',
            'User-Agent': 'okhttp/4.9.3',
            'token': token
        }
        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                result = sign(session, uid)
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
