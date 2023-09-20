"""
cron: 0 10 * * *
new Env('点码广告_看视频')
"""
import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = '点码广告_看视频'
FILE_NAME = '点码广告Token.txt'


def query_task(session: Session, uid: str) -> int:
    url = 'https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/yxapp/ads/getEverydayTask'
    payload = {"userId": uid}
    res = session.post(url, json=payload)
    if res.text.count('tasks'):
        return res.json()['body']['tasks']
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'任务次数查询失败:{msg}')


def complete_task(session: Session, uid: str) -> str:
    url = 'https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/yxapp/ads/addViewCount'
    payload1 = {"adPlatform": "3", "adId": "1723327822", "adType": "3", "pageView": "1", "type": "Android", "viewType": 2,
                "userId": uid}
    payload2 = {"adPlatform": "3", "adId": "1723327822", "adType": "3", "adReward": "1", "type": "Android", "viewType": 2,
                "userId": uid, "taskType": 2}
    res = session.post(url, json=payload1)
    res = session.post(url, json=payload2)
    if res.text.count('state') and res.json()['state'] == 200:
        return '观看视频成功'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'观看视频失败:{msg}')


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
                while True:
                    count = query_task(session, uid)
                    log.info(f'【{index}】{username}----今日已观看: {count} 剩余次数: {45 - count}')
                    if count == 45:
                        return True
                    for i in range(45 - count):
                        result = complete_task(session, uid)
                        log.info(f'【{index}】{username}----{result}*{i + 1}')
            except:
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
