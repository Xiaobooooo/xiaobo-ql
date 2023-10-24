"""
cron: 0 8 2-31/2 * *
new Env('Avive_领取空投')
"""
from requests import Session

from DL_AviveMining import get_params, get_headers, FILE_NAME
from common.task import QLTask
from common.util import log, get_android_session, get_error_msg

TASK_NAME = "Avive_领取空投"


def receive(session: Session, mac: str, did: str, token: str) -> str:
    name = '领取空投'
    url = "https://api.avive.world/v1/mint/collect/?" + get_params(mac, did)
    res = session.post(url, headers=get_headers(url, token))
    if res.text.count('code') and res.json().get('code') == 0 and res.text.count('{}'):
        return f'{name}成功'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        mac = split[-3]
        did = split[-2]
        token = split[-1]

        session = get_android_session()
        session.proxies = {"https": proxy}
        result = receive(session, mac, did, token)
        log.info(f"【{index}】{result}")


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
