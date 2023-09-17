"""
cron: 0 5 * * *
new Env('兔贝尔_抽奖')
"""
import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = "兔贝尔_抽奖"
FILE_NAME = "兔贝尔Token.txt"


def draw(session: Session) -> str:
    res = session.post('https://www.tber.shop/api/task/lottery/draw')
    if res.text.count('win_value'):
        value = res.json()['data']['win_value']
        return f'抽奖成功: {value}'
    if res.text.count('抽奖次数不足'):
        return f'抽奖次数不足'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'抽奖失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[len(split) - 1]
        log.info(f"【{index}】{username}----正在完成任务")

        session = requests.session()
        session.headers = {
            'token': token,
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {"https": proxy}
            try:
                result = draw(session)
                log.info(f"【{index}】{username}----{result}")
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
