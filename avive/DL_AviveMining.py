"""
cron: 0 8 1-31/2 * *
new Env('Avive_开启空投')
"""
import requests
from requests import Session

from DL_AviveDaily import get_params, get_headers
from common.task import QLTask, get_proxy
from common.util import log, log_exc

TASK_NAME = "Avive_开启空投"
FILE_NAME = "AviveToken.txt"


def mining(session: Session, mac: str, did: str, token: str) -> str:
    url = "https://api.avive.world/v1/mint/start/?" + get_params(mac, did)
    res = session.post(url, headers=get_headers(url, token))
    if res.text.count('code') and res.json()['code'] == 0 and res.text.count('{}'):
        return '空投开启成功'
    msg = res.json()['err_msg'] if res.text.count('err_msg') else res.text
    raise Exception(f'空投开启失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        mac = split[-3]
        did = split[-2]
        token = split[-1]
        log.info(f"【{index}】{username}----正在完成任务")

        session = requests.session()
        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {"https": proxy}
            try:
                result = mining(session, mac, did, token)
                log.info(f"【{index}】{username}----{result}")
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
