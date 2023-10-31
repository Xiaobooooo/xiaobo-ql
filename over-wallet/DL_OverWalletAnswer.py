"""
cron: 33 6 * * *
new Env('OverWallet_答题')
"""
from tls_client import Session

from common.task import QLTask
from common.util import log, lock, get_error_msg, get_android_session

TASK_NAME = 'OverWallet_答题'
FILE_NAME = 'OverWalletToken.txt'

quiz_id = ''
answer_id = ''


def answer(session: Session) -> str:
    global quiz_id, answer_id

    if quiz_id == '':
        name = '查询ID'
        res = session.get('https://mover-api-prod.over.network/mission/3/info')
        if res.text.count('quiz_id'):
            quiz_id = res.json()['data']['quiz_id']
        else:
            return get_error_msg(name, res)

    res = None
    name = '答题'
    if answer_id == '':
        for i in range(3):
            ans = f'{i + 1}'
            payload = {"answer_list": [ans]}
            res = session.post(f'https://mover-api-prod.over.network/mission/3/quiz/{quiz_id}/submit', json=payload)
            if res.text.count('reward') and res.json()['data']['reward'] is not None:
                answer_id = ans
                reward = res.json()['data']['reward']
                return f'{name}成功: {reward}'
    else:
        payload = {"answer_list": [answer_id]}
        res = session.post(f'https://mover-api-prod.over.network/mission/3/quiz/{quiz_id}/submit', json=payload)
        if res.text.count('reward') and res.json()['data']['reward'] is not None:
            reward = res.json()['data']['reward']
            return f'{name}成功: {reward}'
    if res.text.count('code') and (res.json().get('code') == -14 or res.json().get('code') == -26):
        return f'{name}时间未到'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        headers = {
            'client-version': '1.0.6.53',
            'User-Agent': 'okhttp/4.9.2',
            'authorization': f'Bearer {token}',
        }
        session = get_android_session()
        session.headers.update(headers)
        session.proxies = {'https': proxy}

        result = answer(session)
        log.info(f'【{index}】{result}')
        if result.count('时间未到'):
            with lock:
                self.wait += 1


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
