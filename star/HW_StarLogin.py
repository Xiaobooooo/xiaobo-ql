"""
cron: 1 1 1 1 1
new Env('Star_登录')
"""
import hashlib
import json
import time

import requests
from tls_client import Session
from tls_client.response import Response

from common.task import QLTask
from common.util import log, write_txt, get_error_msg, UnAuthException

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
    return get_error_msg(name, res, un_auths=['You are not authr'], **kwargs)


def get_headers(token: str = '') -> dict:
    return {'User-Agent': 'Dart/2.19 (dart:io)', 'Authorization': f'Bearer {token}'}


def login(session: Session, username: str, password: str) -> str:
    name = '登录'
    payload = encrypt({'email': username, 'password': password})
    res = session.post('https://api.starnetwork.io/v3/email/login_check', json=payload)
    if res.text.count('jwt'):
        body = res.json()
        if body.get('status') == 'blocked':
            raise UnAuthException(name)
        if body.get('status') == 'registered':
            return body.get('jwt')
    if res.text.count('email_password_incorrect'):
        return '登录: 邮箱或密码错误'
    raise get_error(name, res)


def get_uid(session: Session):
    name = '获取ID'
    res = session.get('https://api.starnetwork.io/v3/auth/user')
    if res.text.count('{"id":'):
        return res.json()['id']
    return get_error(name, res)


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name)
        self.success_email = []
        self.fail_email = []

    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        username = split[0]
        password = split[1]
        if not self.fail_email.count(text):
            self.fail_email.append(text)

        session = requests.Session()
        session.headers.update(get_headers())
        session.proxies = {'https': proxy}

        result = login(session, username, password)
        if result.count('登录'):
            log.info(f'【{index}】{result}')
            return result
        log.info(f'【{index}】登录: 成功')
        session.headers.update({'Authorization': f'Bearer {result}'})
        uid = get_uid(session)
        log.info(f'【{index}】获取ID: 成功')
        self.fail_email.remove(text)
        self.success_email.append(f'{username}----{password}----{uid}----{result}')

    def save(self):
        log.info(f'-----账号文本-----')
        write_txt('StarNetwork', '')
        if self.success_email:
            log.info(f'-----成功文本-----')
            write_txt('StarNetworkToken', ''.join([f'{email}\n' for email in self.success_email]), True)
        if self.un_auth:
            log.info(f'-----封禁文本-----')
            for un_auth in self.un_auth:
                if self.fail_email.count(un_auth):
                    self.fail_email.remove(un_auth)
            write_txt('StarNetwork已封禁', ''.join([f'{un_auth}\n' for un_auth in self.un_auth]), True)
        if self.fail_email:
            log.info(f'-----失败文本-----')
            write_txt('StarNetwork登录失败', ''.join([f'{email}\n' for email in self.fail_email]), True)


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
