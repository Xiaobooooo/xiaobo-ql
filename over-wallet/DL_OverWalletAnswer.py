"""
cron: 33 8 * * *
new Env('OverWallet_答题')
"""
from tls_client import Session

from DL_OverWalletSign import get_headers
from common.task import QLTask
from common.util import log, get_error_msg, get_android_session, CompletedOrWaitingException

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
            quiz_id = res.json().get('data').get('quiz_id')
        else:
            return get_error_msg(name, res)

    res = None
    name = '答题'
    if answer_id == '':
        for i in range(3):
            ans = f'{i + 1}'
            payload = {"answer_list": [ans]}
            res = session.post(f'https://mover-api-prod.over.network/mission/3/quiz/{quiz_id}/submit', json=payload)
            if res.text.count('reward') and res.json().get('data').get('reward') is not None:
                answer_id = ans
                reward = res.json().get('data').get('reward')
                return f'{name}: {reward} Point'
    else:
        payload = {"answer_list": [answer_id]}
        res = session.post(f'https://mover-api-prod.over.network/mission/3/quiz/{quiz_id}/submit', json=payload)
        if res.text.count('reward') and res.json().get('data').get('reward') is not None:
            reward = res.json().get('data').get('reward')
            return f'{name}: {reward} Point'
    if res.text.count('code') and (res.json().get('code') == -14 or res.json().get('code') == -26):
        raise CompletedOrWaitingException(name)
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        session = get_android_session()
        session.headers.update(get_headers(token))
        session.proxies = proxy

        result = answer(session)
        log.info(f'【{index}】{result}')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
