"""
cron: 15 9 * * *
new Env('恒贵_签到R')
"""
import base64
import json
import time
from concurrent import futures

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from common.task import QLTask, get_proxy
from common.util import log, log_exc, get_env

TASK_NAME = '恒贵_签到R'
FILE_NAME = '恒贵Token.txt'

KEY = 'AAAAAAAABBBBBBBB'.encode('utf-8')
IV = 'CCCCCC_AAAAABBBB'.encode('utf-8')


def decrypt(data: str) -> str:
    try:
        aes = AES.new(key=KEY, mode=AES.MODE_CBC, iv=IV)
        data = base64.b64decode(data)
        text = aes.decrypt(data)
        result = unpad(text, AES.block_size, style='pkcs7')
        return result.decode('utf-8')
    except:
        log.error(f'解密失败: {log_exc()}   原数据: {data}')
        return data


def sign(token: str, proxy: str) -> str:
    session = requests.session()
    session.headers = {
        'Authorization': token,
        'User-Agent': 'okhttp/3.12.1'
    }
    session.proxies = {"https": proxy}
    res = session.post('http://line2.qdfgk.com/Home/Index/t5_qiandao')
    return res.text


class Task(QLTask):
    def __init__(self, task_name: str, file_name: str):
        super().__init__(task_name, file_name)
        log.info('=====加载恒贵配置=====')
        datas = get_env('恒贵配置').split('|')
        if len(datas) == 2:
            try:
                self.thread_num = int(datas[0])
                self.thread_num_r = int(datas[1])
                return
            except:
                log.info(f'恒贵配置有误，设置默认配置1|10')
        else:
            log.info(f'未设置恒贵配置，设置默认配置1|10')
        self.thread_num = 1
        self.thread_num_r = 10
        log.info('=====恒贵配置加载完毕=====')

    def task(self, index: int, text: str) -> bool:
        split = text.split('----')
        username = split[0]
        token = split[-1]
        log.info(f'【{index}】{username}----正在完成任务')

        proxy = get_proxy(self.api_url)

        success = 0
        with futures.ThreadPoolExecutor(max_workers=self.thread_num_r) as pool:
            tasks = [pool.submit(sign, token, proxy) for i in range(0, self.thread_num_r)]
            futures.wait(tasks)
            count = 0
            for future in futures.as_completed(tasks):
                count += 1
                try:
                    res = {'res': future.result().replace('"', '')}
                    res = decrypt(res['res'])
                    if res.count('msg'):
                        res_json = json.loads(res)
                        msg = res_json['msg']
                        if res_json['status'] == 1:
                            success += 1
                    else:
                        msg = res
                    log.info(f'【{index}】{username}----[{count}]{msg}')
                except:
                    log.info(f'【{index}】{username}----[{count}]签到失败: {log_exc()}')
        pool.shutdown()
        log.info(f'【{index}】{username}----签到成功数: {success}   延迟5S后结束')
        time.sleep(5)
        return True


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
