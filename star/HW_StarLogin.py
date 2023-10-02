"""
cron: 1 1 1 1 1
new Env('Star_登录')
"""
import hashlib
import json
import time

import requests
from requests import Session

from common.task import QLTask, get_proxy
from common.util import log, log_exc, write_txt

TASK_NAME = 'Star_登录'
FILE_NAME = 'StarNetwork.txt'


def encrypt(payload, is_key: bool = False):
    timestamp = int(time.time() * 1000)
    data = json.dumps(payload).replace(' ', '') + ':D7C92C3FDB52D54147B668DC6F8A5@' + str(timestamp)
    sign = hashlib.md5(data.encode()).hexdigest()
    payload['timestamp'] = timestamp
    payload['key' if is_key else 'hash'] = sign
    return payload


def get_error(text):
    if text.count('Cloudflare to restrict access') > 0 or text.count('You do not have access to') > 0:
        return '访问被拒绝'
    if text.count('You are not authr') > 0:
        return '账号被封禁或登录失效'
    return ''


def login(session: Session, username: str, password: str) -> str:
    payload = encrypt({'email': username, 'password': password})
    res = session.post('https://api.starnetwork.io/v3/email/login_check', json=payload)
    if res.text.count('jwt'):
        if res.json()['status'] == 'blocked':
            return '账号封禁'
        if res.json()['status'] == 'registered':
            token = res.json()['jwt']
            return token
    msg = get_error(res.text)
    if not msg:
        msg = res.json()['message'] if res.text.count('message') else res.text
    raise Exception(f'登录失败:{msg}')


def get_uid(session: Session):
    res = session.get('https://api.starnetwork.io/v3/auth/user')
    if res.text.count('{"id":'):
        uid = res.json()['id']
        return uid
    msg = get_error(res.text)
    if not msg:
        msg = res.json()['message'] if res.text.count('message') else res.text
    raise Exception(f'ID获取失败:{msg}')


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name)
        self.blocked = []
        self.success_email = []

    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        password = split[1]
        log.info(f'【{index}】{username}----正在完成任务')

        session = requests.session()
        session.headers = {'User-Agent': 'Dart/2.19 (dart:io)'}

        proxy = get_proxy(self.api_url)
        for try_num in range(self.max_retries):
            session.proxies = {'https': proxy}
            try:
                result = login(session, username, password)
                if result == '账号封禁':
                    log.info(f'【{index}】{username}----账号封禁')
                    self.blocked.append(f'{text}\n')
                    return False
                log.info(f'【{index}】{username}----登录成功|开始获取ID')
                session.headers['Authorization'] = f'Bearer {result}'
                uid = get_uid(session)
                self.success_email.append(f'{username}----{password}----{uid}----{result}')
                return True
            except:
                if log_exc().count('email_password_incorrect'):
                    self.fail_data.append(f'【{index}】{username}----{password}----密码错误')
                    return False
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】{username}----进行第{try_num + 1}次重试----{log_exc()}')
                    proxy = get_proxy(self.api_url)
                else:
                    log.error(f'【{index}】{username}----重试完毕----{log_exc()}')
                    self.fail_data.append(f'【{index}】{username}----{password}----{log_exc()}')
        return False

    def statistics(self):
        if len(self.blocked) > 0:
            log_data = '-----封禁数据统计-----\n'
            log_data += ''.join([f'{fail}\n' for fail in self.blocked])
            log.info(log_data)
        super().statistics()

    def save(self):
        write_txt('StarNetwork', '')
        if len(self.success_email) > 0:
            log.info(f'-----成功文本-----')
            write_txt('StarNetworkToken', ''.join([f'{email}\n' for email in self.success_email]), True)
        if len(self.blocked) > 0:
            log.info(f'-----封禁文本-----')
            write_txt('StarNetwork已封禁', ''.join([f'{email}\n' for email in self.blocked]), True)
        if len(self.fail_data) > 0:
            log.info(f'-----失败文本-----')
            write_txt('StarNetwork登录失败', ''.join([f'{email[email.index("】") + 1:]}\n' for email in self.fail_data]), True)

    def push_data(self):
        return f'总任务数：{self.total}\n成功数：{self.success}\n失败数：{len(self.fail_data)}\n封禁数：{len(self.blocked)}'


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
