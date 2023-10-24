"""
cron: 0 12 1-31/7 * *
new Env('Avive_每周奖励')
"""
import json

from requests import Session

from DL_AviveMining import get_params, get_headers, FILE_NAME
from common.task import QLTask
from common.util import log, lock, get_android_session, get_error_msg

TASK_NAME = 'Avive_每周奖励'


def weekly(session: Session, mac: str, did: str, token: str) -> str:
    name = '领取奖励'
    payload = {'bonus_type': 1}
    url = 'https://api.avive.world/v1/mint/task/bonus/collect/?' + get_params(mac, did, json.dumps(payload))
    res = session.post(url, json=payload, headers=get_headers(url, token))
    if res.text.count('code') and res.json().get('code') == 0 and res.text.count('{}'):
        return f'{name}成功'
    if res.text.count('invalid collect operation'):
        return f'{name}时间未到'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        mac = split[-3]
        did = split[-2]
        token = split[-1]

        session = get_android_session()
        session.proxies = {'https': proxy}
        result = weekly(session, mac, did, token)
        log.info(f'【{index}】{result}')
        if result.count('时间未到'):
            with lock:
                self.wait += 1


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
