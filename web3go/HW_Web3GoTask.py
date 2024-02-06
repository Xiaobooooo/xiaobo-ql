"""
cron: 0 0 1 1/1 *
new Env('Web3Go_任务')
"""
import json
import random
import string

import requests
from tls_client import Session
from web3 import Web3

from common.task import QLTask
from common.util import log, get_error_msg, get_chrome_session
from HW_Web3GoCheckIn import login

TASK_NAME = 'Web3Go_任务'
FILE_NAME = 'Web3GoWallet.txt'


def set_email(session: Session) -> json:
    name = '设置邮箱'
    username = ''.join(random.sample(string.ascii_lowercase, random.randint(6, 10)))
    res = session.post('https://reiki.web3go.xyz/api/profile', json={"email": f"{username}@rambler.cc", "name": username})
    if res.text == '[]' or res.text.count('openedAt'):
        return res.json()
    return get_error_msg(name, res)


def get_gift(session: Session) -> json:
    name = '获取礼物'
    res = session.get('https://reiki.web3go.xyz/api/gift?type=recent')
    if res.text == '[]' or res.text.count('openedAt'):
        return res.json()
    return get_error_msg(name, res)


def open_gift(session: Session, gift_id: str):
    name = '打开礼物'
    res = session.post(f'https://reiki.web3go.xyz/api/gift/open/{gift_id}')
    if res.text == 'true':
        return f'{name}: 成功'
    return get_error_msg(name, res)


def get_questions(session: Session) -> json:
    name = '获取问题列表'
    res = session.get('https://reiki.web3go.xyz/api/quiz')
    if res.text == '[]' or res.text.count('currentProgress'):
        return res.json()
    return get_error_msg(name, res)


def get_answers(session: Session, quiz_id: str) -> json:
    name = '获取答题列表'
    res = session.get(f'https://reiki.web3go.xyz/api/quiz/{quiz_id}')
    if res.text.count('items'):
        return res.json().get('items')
    return get_error_msg(name, res)


def answer(session: Session, quiz_id: str, _answer: str) -> bool:
    name = '答题'
    payload = {"answers": [_answer]}
    res = session.post(f'https://reiki.web3go.xyz/api/quiz/{quiz_id}/answer', json=payload)
    if res.text.count('Answer correct'):
        return True
    if res.text.count('Already answered'):
        return True
    if res.text.count('Invalid answer'):
        return False
    get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        address = Web3.to_checksum_address(split[0])
        private_key = split[1]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36'
        }
        # session = get_chrome_session()
        session = requests.Session()
        session.headers.update(headers)
        session.proxies = {'https': proxy}
        token = login(session, address, private_key)
        log.info(f'【{index}】登录成功')
        session.headers.update({'Authorization': 'Bearer ' + token})

        gifts = get_gift(session)
        for gift in gifts:
            if not gift.get('openedAt'):
                open_gift(session, gift.get('id'))
                log.info(f'【{index}】打开礼物[{gift.get("id")}]: 成功')

        questions = get_questions(session)
        for question in questions:
            if question.get('currentProgress') < question.get('totalItemCount'):
                question_id = question.get('id')
                items = get_answers(session, question_id)
                for i in range(question.get('currentProgress'), len(items)):
                    items_id = items[i].get('id')
                    if items_id == 'c9af4601-ea03-49c8-82e2-95f55074e703':
                        result = answer(session, items_id, address)
                        log.info(f'【{index}】填写地址: {"成功" if result else "失败"}')
                    else:
                        for k, v in items[i].get('options').items():
                            result = answer(session, items_id, k)
                            if result:
                                break
                log.info(f'【{index}】答题[{question_id}]: 成功')


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
