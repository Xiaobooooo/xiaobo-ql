import logging
import os
import random
import sys
import threading
import time

import tls_client
from tls_client.response import Response

logging.basicConfig(level=logging.INFO, datefmt="%H:%M:%S", format='%(asctime)s %(message)s')
log = logging.getLogger()

lock = threading.RLock()


class UnAuthorizationException(Exception):
    pass


def load_txt(file_name: str) -> list:
    """
    读取文本
    :param file_name: 文件名
    :return: 文本数组
    """
    if not file_name.endswith('.txt'):
        file_name += '.txt'
    lines = []
    log.info(f"正在读取<{file_name}>文件")
    while os.path.exists(file_name) is False:
        log.error(f"不存在<{file_name}>文件，3秒后重试")
        time.sleep(3)
    with open(sys.path[0] + "/" + file_name, "r+") as f:
        while True:
            line = f.readline().strip()
            if line is None or line == '':
                break
            lines.append(line)
    log.info(f'文本读取完毕，总计数量: {len(lines)}')
    return lines


def write_txt(file_name: str, text: str, append: bool = False) -> bool:
    """
    写入文本
    :param file_name: 文本名
    :param text: 写入文本内容
    :param append: 是否追加
    :return: 写入结果
    """
    if not file_name.endswith('.txt'):
        file_name += '.txt'
    mode = 'a+' if append else 'w+'
    log.info(f"正在写入<{file_name}>文件")
    with lock:
        try:
            with open(sys.path[0] + '/' + file_name, mode) as f:
                f.write(text)
            return True
        except BaseException as e:
            log.error(f"文本写入失败:{repr(e)}")
            return False


def del_file(file_name: str) -> bool:
    """
    删除文本
    :param file_name: 文件名
    :return: 删除结果
    """
    if not file_name.endswith('.txt'):
        file_name += '.txt'
    log.info(f"正在删除<{file_name}>文件")
    if os.path.isfile(file_name):
        try:
            os.remove(file_name)  # 这个可以删除单个文件，不能删除文件夹
            return True
        except BaseException as e:
            log.error(f"文件删除失败:{repr(e)}")
    else:
        log.error(f"{file_name}不存在或不是一个文件")
    return False


def get_env(env_name: str) -> str:
    """
    获取环境变量
    :param env_name: 环境变量名
    :return: 环境变量值
    """
    log.info(f"正在读取环境变量【{env_name}】")
    try:
        if env_name in os.environ:
            env_val = os.environ[env_name]
            if len(env_val) > 0:
                log.info(f"读取到环境变量【{env_name}】")
                return env_val
        log.info(f"暂未设置环境变量【{env_name}】")
    except Exception as e:
        log.error(f"环境变量【{env_name}】读取失败: {repr(e)}")
    return ''


def get_error_msg(name: str, response: Response, un_auths: list = None, msg_key: str = None, is_raise: bool = True) -> str:
    """
    获取响应中的错误消息，并抛出异常
    :param name: 操作
    :param response: 响应
    :param un_auths: 未登录标识
    :param msg_key: 消息key
    :param is_raise: 是否抛出防火墙拦截
    :return: 错误信息
    """
    msg = None
    text = response.text.strip()
    body = response.json() if text.startswith('{') and text.endswith('}') else {}
    if body:
        if msg_key:
            msg = body.get(msg_key)
        else:
            msg = body.get('msg') if body.get('msg') else body.get('message')
    if not msg:
        msg = text

    intercepts = ['You are unable to access', 'Cloudflare to restrict access', 'You do not have access to']
    for intercept in intercepts:
        if text.count(intercept):
            msg = '请求被拦截'

    un_login = ['未登录', '登录失效', '无效Token', '请先登录', '请登录后操作']
    if un_auths:
        un_login.extend(un_auths)
    for un_auth in un_login:
        if text.lower().count(un_auth.lower()):
            raise UnAuthorizationException(f'{name}失败: 账号登录过期或被冻结、封禁')

    msg = f'{name}失败: {msg}'
    if is_raise:
        raise Exception(msg)
    return msg


def get_except(only_msg: bool = False):
    except_type, except_value, except_traceback = sys.exc_info()
    if only_msg:
        return except_value
    return f'{except_type.__name__}({except_value})'


def get_random_session(client_list: list = None):
    if not client_list:
        return get_chrome_session()
    client = client_list[random.randint(0, len(client_list) - 1)]
    return tls_client.Session(client_identifier=client, random_tls_extension_order=True)


def get_chrome_session():
    chrome_list = ['chrome_103', 'chrome_104', 'chrome_105', 'chrome_106', 'chrome_107', 'chrome_108', 'chrome109', 'Chrome110',
                   'chrome111', 'chrome112']
    return get_random_session(chrome_list)


def get_android_session():
    android_list = ['okhttp4_android_7', 'okhttp4_android_8', 'okhttp4_android_9', ' okhttp4_android_10', 'okhttp4_android_11',
                    'okhttp4_android_12', 'okhttp4_android_13']
    return get_random_session(android_list)


def get_ios_session():
    ios_list = ['safari_ios_15_5', 'safari_ios_15_6', 'safari_ios_16_0']
    return get_random_session(ios_list)
