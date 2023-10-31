"""
cron: 30 2-23/5 * * *
new Env('Eagle_挖矿')
"""
import time

from tls_client import Session

from common.task import QLTask
from common.util import log, lock, get_error_msg, get_android_session

TASK_NAME = "Eagle_挖矿"
FILE_NAME = "EagleToken.txt"


def mining(session: Session) -> str:
    name = '挖矿'
    res = session.post("https://eaglenetwork.app/api/start-mining", json={})
    if res.text.count('start_time') > 0:
        return f'{name}成功'
    if res.text.count('Mining Already Started') > 0:
        return f'{name}时间未到'
    return get_error_msg(name, res)


class Task(QLTask):
    def task(self, index: int, text: str, proxy: str):
        split = text.split('----')
        token = split[-1]

        headers = {
            'UserAgent': 'android 1.0.65',
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; HD1910 Build/PQ3B.190801.002)',
            'AuthToken': token
        }
        session = get_android_session()
        session.headers.update(headers)
        session.proxies = {"https": proxy}

        result = mining(session)
        log.info(f"【{index}】{result}，延迟1秒后结束")
        if result.count('时间未到'):
            with lock:
                self.wait += 1
        time.sleep(1)


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
