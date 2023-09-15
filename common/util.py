import logging
import os
import sys
import threading
import time

logging.basicConfig(level=logging.INFO, datefmt="%H:%M:%S", format='%(asctime)s [%(lineno)d] %(levelname)s %(message)s')
log = logging.getLogger()

lock = threading.RLock()


def load_txt(file_name: str) -> list[str]:
    """
    读取文本
    :param file_name: 文件名
    :return: 文本数组
    """
    if not file_name.endswith('.txt'):
        file_name += '.txt'
    lines = []
    log.info(f"正在读取{file_name}文件")
    while os.path.exists(file_name) is False:
        log.error(f"不存在{file_name}文件，3秒后重试")
        time.sleep(3)

    with open(sys.path[0] + "/" + file_name, "r+") as f:
        while True:
            line = f.readline().strip()
            if line is None or line == '':
                break
            lines.append(line)
    log.info(f'文本读取完毕，总计数量: {len(lines)}')
    return lines


def write_txt(file_name: str, text: str, append: bool = True) -> bool:
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
    log.info(f"正在写入{file_name}文件")
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
    log.info(f"正在删除{file_name}文件")
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


def log_exc():
    except_type, except_value, except_traceback = sys.exc_info()
    except_file = os.path.split(except_traceback.tb_frame.f_code.co_filename)[1]
    return f'{except_file}_{except_traceback.tb_lineno}:{except_value}'
