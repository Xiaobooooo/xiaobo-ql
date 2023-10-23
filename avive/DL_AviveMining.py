"""
cron: 0 8 1-31/2 * *
new Env('Avive_开启空投')
"""
import hashlib
import random
import string
import time
from urllib.parse import urlencode

from tls_client import Session

from common.task import QLTask
from common.util import log, get_android_session, get_error_msg

TASK_NAME = "Avive_开启空投"
FILE_NAME = "AviveToken.txt"


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
    request_url = 'https://api.xiaobooooo.com/avive/api/getHostEnv?timestamp=' + timestamp + '&nonce=' + nonce
    res = get_android_session().post(request_url, json={'url': url})
    if res.text.count('hostEnv'):
        host_env = res.json()['data']['hostEnv']
        sid = res.json()['data']['sid']
        sig = res.json()['data']['sig']
        headers['Request-Sig'] = sig
        headers['Request-Sid'] = sid
        headers['Host-Env'] = str(host_env)
    return headers


def mining(session: Session, mac: str, did: str, token: str) -> str:
    name = '开启空投'
    url = "https://api.avive.world/v1/mint/start/?" + get_params(mac, did)
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
        result = mining(session, mac, did, token)
        log.info(f"【{index}】{result}")


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
