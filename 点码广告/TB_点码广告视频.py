"""
cron: 0 10 * * *
new Env('点码广告_看视频')
"""
import time
from concurrent import futures

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock
from 点码广告.TB_点码广告签到 import get_sign

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


def query_complete_task(session: Session, uid: str) -> str:
    url = 'https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/yxapp/ads/getEverydayTaskCount'
    payload = {"userId": uid, "timestamp": 1695830719771, "sign": "5d28885804ce490372dfce906502eeff"}
    res = session.post(url, json=payload)
    if res.text.count('state') and res.json()['state'] == 200:
        return res.json()['body']
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'未结算数量查询失败:{msg}')


def complete_task(session: Session, uid: str) -> str:
    url = 'https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/yxapp/ads/addEverydayTaskCount'
    timestamp = int(time.time() * 1000)
    payload = {"userId": uid, "timestamp": timestamp, "sign": get_sign(f'{uid}_AndroidCount{timestamp}')}
    res = session.post(url, json=payload)
    if res.text.count('state') and res.json()['state'] == 200:
        return '观看视频成功'
    if res.text.count('您的访问被阻断'):
        return '访问被阻断'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'观看视频失败:{msg}')


def confirm_task(session: Session, uid: str, count: int) -> str:
    url = 'https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/yxapp/ads/addEverydayTask'
    timestamp = int(time.time() * 1000)
    payload = {"tasks": count, "type": "Android", "userId": uid, "timestamp": timestamp,
               "sign": get_sign(f'{uid}_Android{timestamp}')}
    res = session.post(url, json=payload)
    if res.text.count('state') and res.json()['state'] == 200:
        return '任务结算成功'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'任务结算失败:{msg}')

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
                        break
                    for i in range(45 - count):
                        result = complete_task(session, uid)
                        if result.count('访问被阻断'):
                            proxy = get_proxy(self.api_url)
                            session.proxies = {'https': proxy}
                        log.info(f'【{index}】{username}----{result}*{i + 1}')
                    time.sleep(5)
                    count = query_complete_task(session, uid)
                    log.info(f'【{index}】{username}----未结算数量: {count}')
                    # confirm_task(session, uid, int(count))
                    self.thread_num_r = 5
                    with futures.ThreadPoolExecutor(max_workers=self.thread_num_r) as pool:
                        tasks = [pool.submit(confirm_task, session, uid, int(count)) for i in range(0, self.thread_num_r)]
                        futures.wait(tasks)
                        for future in futures.as_completed(tasks):
                            try:
                                log.info(f'【{index}】{username}----{future.result()}')
                            except:
                                log.info(f'【{index}】{username}----{log_exc()}')
                    pool.shutdown()
                return True
            except Exception as e:
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                    proxy = get_proxy(self.api_url)
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
