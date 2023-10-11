"""
cron: 33 6 * * *
new Env('OverWallet_答题')
"""
import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = 'OverWallet_答题'
FILE_NAME = 'OverWalletToken.txt'

quiz_id = ''
answer_id = ''


def answer(session: Session) -> str:
    global quiz_id, answer_id
    if quiz_id == '':
        res = session.get('https://mover-api-prod.over.network/mission/3/info')
        if res.text.count('quiz_id'):
            quiz_id = res.json()['data']['quiz_id']
        else:
            msg = res.json()['msg'] if res.text.count('msg') else res.text
            raise Exception(f'ID查询失败:{msg}')
    res = None
    if answer_id == '':
        for i in range(3):
            ans = f'{i + 1}'
            payload = {"answer_list": [ans]}
            res = session.post(f'https://mover-api-prod.over.network/mission/3/quiz/{quiz_id}/submit', json=payload)
            if res.text.count('reward') and res.json()['data']['reward'] is not None:
                answer_id = ans
                reward = res.json()['data']['reward']
                return f'答题成功: {reward}'
    else:
        payload = {"answer_list": [answer_id]}
        res = session.post(f'https://mover-api-prod.over.network/mission/3/quiz/{quiz_id}/submit', json=payload)
        if res.text.count('reward') and res.json()['data']['reward'] is not None:
            reward = res.json()['data']['reward']
            return f'答题成功: {reward}'
    if res.text.count('code') and (res.json()['code'] == -14 or res.json()['code'] == -26):
        return '答题时间未到'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'答题失败:{msg}')


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
                result = answer(session)
                if result.count('时间未到'):
                    with lock:
                        self.wait += 1
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
