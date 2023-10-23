"""
cron: 1 1 1 1 1
new Env('Star_登录')
"""
import hashlib
import json
import time

import requests
from requests import Session, Response

from common.task import QLTask
from common.util import log, write_txt, get_error_msg, UnAuthorizationException

TASK_NAME = 'Star_登录'
FILE_NAME = 'StarNetwork.txt'


def encrypt(payload, is_key: bool = False):
    timestamp = int(time.time() * 1000)
    data = json.dumps(payload).replace(' ', '') + ':D7C92C3FDB52D54147B668DC6F8A5@' + str(timestamp)
    sign = hashlib.md5(data.encode()).hexdigest()
    payload['timestamp'] = timestamp
    payload['key' if is_key else 'hash'] = sign
    return payload


def get_error(name: str, res: Response, **kwargs):
    return get_error_msg(name, res, ['You are not authr'], **kwargs)


def login(session: Session, username: str, password: str) -> str:
    name = '登录'
    payload = encrypt({'email': username, 'password': password})
    res = session.post('https://api.starnetwork.io/v3/email/login_check', json=payload)
    if res.text.count('jwt'):
        body = res.json()
        if body.get('status') == 'blocked':
            return f'登录失败: 账号封禁'
        if body.get('jwt')['status'] == 'registered':
            return res.json().get('jwt')
    raise get_error(name, res)


def get_uid(session: Session):
    name = '获取ID'
    res = session.get('https://api.starnetwork.io/v3/auth/user')
    if res.text.count('{"id":'):
        uid = res.json()['id']
        return uid
    return get_error(name, res)


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name)
        self.blocked = []
        self.success_email = []
        self.fail_email = []

    def task(self, index: int, text: str, proxy: str):
        if not self.fail_email.count(text):
            self.fail_email.append(text)

        split = text.split('----')
        username = split[0]
        password = split[1]

        session = requests.session()
        session.headers.update({'User-Agent': 'Dart/2.19 (dart:io)'})
        session.proxies = {'https': proxy}

        result = login(session, username, password)
        if result.count('账号封禁'):
            self.blocked.append(text)
            raise UnAuthorizationException(result)
        log.info(f'【{index}】登录成功|开始获取ID')
        session.headers.update({'Authorization': f'Bearer {result}'})
        uid = get_uid(session)
        self.success_email.append(f'{password}----{uid}----{result}')

    def statistics(self):
        if len(self.blocked) > 0:
            log_data = '-----封禁数据统计-----\n'
            log_data += ''.join([f'{fail}\n' for fail in self.blocked])
            log.info(log_data)
        super().statistics()

    def save(self):
        log.info(f'-----账号文本-----')
        write_txt('StarNetwork', '')
        if self.success_email:
            log.info(f'-----成功文本-----')
            write_txt('StarNetworkToken', ''.join([f'{email}\n' for email in self.success_email]), True)
        if self.blocked:
            log.info(f'-----封禁文本-----')
            write_txt('StarNetwork已封禁', ''.join([f'{email}\n' for email in self.blocked]), True)
        if self.fail_data:
            log.info(f'-----失败文本-----')
            write_txt('StarNetwork登录失败', ''.join([f'{email}\n' for email in self.fail_email]), True)

    def push_data(self):
        return f'总任务数：{self.total}\n成功数：{self.success}\n失败数：{len(self.fail_data)}\n封禁数：{len(self.blocked)}'


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
