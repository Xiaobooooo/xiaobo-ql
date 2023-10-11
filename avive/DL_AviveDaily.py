"""
cron: 0 12 1-31/2 * *
new Env('Avive_每日奖励')
"""
import hashlib
import json
import random
import string
import time
from urllib.parse import urlencode

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, lock

TASK_NAME = 'Avive_每日奖励'
FILE_NAME = 'AviveToken.txt'


def get_params(mac: str, did: str, data: str = None) -> str:
    params = {'os': 'android', 'download_channel': 'GooglePlay', 'timezone': 'GMT+08:00', 'ui_lang': 'zh_Hans', 'ntype': 'WIFI',
              'pkg': 'com.meta.avive', 'version': '1.1.1', 'vcode': 21, 'mac': mac, 'operator': 'CHINA+MOBILE', 'os_v': 28,
              'ede_valid': 1, 'app_channel': 'GooglePlay', 'dse_valid': 0, 'open_session': did + str(int(time.time())),
              'android_id': did, 'brand': 'OnePlus', 'device': 'HD1910', 'aid': '', 'code_by_sim': 'CN', 'did': did}
    if data is not None:
        params['r_bd_md5'] = hashlib.md5(data.encode('utf-8')).hexdigest()
    return urlencode(params)


def get_headers(url: str, token: str):
    timestamp = str(int(time.time()))
    nonce = ''.join(random.sample(string.ascii_letters + string.digits, 20))
    headers = {
        'Authorization': 'HIN ' + token,
        'Request-Sgv': '2',
        'Host': 'api.avive.world',
        'User-Agent': 'okhttp/4.6.0',
        'timestamp': timestamp,
        'nonce': nonce
    }
    payload = {'url': url}
    res = requests.post('https://api.xiaobooooo.com/avive/api/getHostEnv?timestamp=' + timestamp + '&nonce=' + nonce, json=payload)
    if res.text.count('hostEnv'):
        host_env = res.json()['data']['hostEnv']
        sid = res.json()['data']['sid']
        sig = res.json()['data']['sig']
        headers['Request-Sig'] = sig
        headers['Request-Sid'] = sid
        headers['Host-Env'] = str(host_env)
    return headers


def daily(session: Session, mac: str, did: str, token: str) -> str:
    payload = {'bonus_type': 1}
    url = 'https://api.avive.world/v1/mint/task/bonus/collect/?' + get_params(mac, did, json.dumps(payload))
    res = session.post(url, json=payload, headers=get_headers(url, token))
    if res.text.count('code') and res.json()['code'] == 0 and res.text.count('{}'):
        return '奖励领取成功'
    if res.text.count('invalid collect operation'):
        return '领取时间未到'
    msg = res.json()['err_msg'] if res.text.count('err_msg') else res.text
    raise Exception(f'奖励领取失败:{msg}')


class Task(QLTask):
    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        mac = split[-3]
        did = split[-2]
        token = split[-1]
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                result = daily(session, mac, did, token)
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
