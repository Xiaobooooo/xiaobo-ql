"""
cron: 30 1-23/4 * * *
new Env('AI宇宙_领取')
"""
import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc

TASK_NAME = 'AI宇宙_领取'
FILE_NAME = 'AI宇宙Token.txt'


def query(session: Session, token: str) -> list:
    res = session.post('http://ai.wecyan.com/index/index', data={'token': token})
    if res.text.count('remain'):
        ids = [value['id'] for value in res.json()['data']['list']]
        return ids
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'查询失败:{msg}')


def collect(session: Session, token: str, cid: str):
    res = session.post('http://ai.wecyan.com/user/collect', data={'token': token, 'id': cid})
    if res.text.count('status') and res.json()['status'] == 1:
        return f'{cid}领取成功'
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'领取失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[len(split) - 1]
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                while True:
                    log.info(f'【{index}】{username}----正在查询ID')
                    ids = query(session, token)
                    if len(ids):
                        log.info(f'【{index}】{username}----正在领取')
                        [log.info(f'【{index}】{username}----{collect(session, token, cid)}') for cid in ids]
                    else:
                        log.info(f'【{index}】{username}----所有奖励领取完毕')
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
