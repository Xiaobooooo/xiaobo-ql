"""
cron: 0 12 * * *
new Env('点码广告_提现')
"""
import re

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = '点码广告_提现'
FILE_NAME = '点码广告Token.txt'


def query(session: Session) -> float:
    res = session.post('https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/wechatapp/account/getuserinfo', json={})
    if res.text.count('incomeBalance'):
        return res.json()['body']['incomeBalance']
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'余额查询失败:{msg}')


def withdrawal(session: Session, money: str) -> str:
    url = 'https://wxsq.itaoniu.com.cn/TN_WANGCAI/api/v2/wechatapp/my/takecash'
    payload = {"money": money}
    res = session.post(url, json=payload)
    if res.text.count('state') and res.json()['state'] == 200:
        return '提现成功'
    if res.text.count('超过日提现最高额度') or res.text.count('商户单日转账额度'):
        return res.json()['msg']
    msg = res.json()['msg'] if res.text.count('msg') else res.text
    raise Exception(f'提现失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[-1]
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {
            'Version': 'wangcai-2.0.0v',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 9; HD1910 Build/PQ3B.190801.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36 MMWEBID/4706 MicroMessenger/8.0.41.2441(0x28002950) WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64 MiniProgramEnv/android',
            'apptoken': token
        }
        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                balance = query(session)
                log.info(f'【{index}】{username}----余额: {balance} {"进行提现" if balance >= 0.3 else "不进行提现"}')
                if balance >= 0.3:
                    if balance >= 10:
                        balance = 10.001
                    result = withdrawal(session, re.findall(r"\d{1,}?\.\d{2}", str(balance))[0])
                    log.info(f'【{index}】{username}----{result}')
                    return True
                with lock:
                    self.wait += 1
                return True
            except:
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{log_exc()}')
        return False

    def push_data(self):
        return f'总任务数：{self.total}\n成功数：{self.success} (其中余额不足提现数：{self.wait})\n失败数：{len(self.fail_data)}'


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
