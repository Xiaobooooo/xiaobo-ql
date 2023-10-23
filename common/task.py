import re
import time
from abc import ABCMeta, abstractmethod
from concurrent import futures

from common.notify import send
from common.util import log, lock, load_txt, get_env, get_except, get_random_session, UnAuthorizationException

ENV_THREAD_NUMBER = 'THREAD_NUMBER'
ENV_PROXY_API = 'PROXY_API'
ENV_DISABLE_PROXY = 'DISABLE_PROXY'
ENV_MAX_RETRIES = 'MAX_RETRIES'
MAX_RETRIES = 3

proxies = []


def get_max_retries() -> int:
    value = get_env(ENV_MAX_RETRIES)
    if value != '':
        try:
            return int(value)
        except:
            log.info(f'重试次数设置有误，设置默认数量{MAX_RETRIES}')
    else:
        log.info(f'暂未设置重试次数，设置默认数量{MAX_RETRIES}')
    return MAX_RETRIES


def get_thread_number(task_num: int) -> int:
    """
    获取线程数
    :param task_num: 任务数量
    :return: 线程数
    """
    thread_num = 5
    value = get_env(ENV_THREAD_NUMBER)
    if value != '':
        try:
            thread_num = int(value)
        except:
            log.info(f'线程数设置有误，设置默认数量{thread_num}')
    else:
        log.info(f'暂未设置线程数，设置默认数量{thread_num}')

    if thread_num > task_num:
        thread_num = task_num
        log.info(f'线程数量大于文本数量，设置文本数量{task_num}')

    if thread_num < 1:
        thread_num = 1
        log.info('线程数量不能小于0，设置最低数量1')

    return thread_num


def get_proxy_api(task_name=None) -> str:
    """
    获取代理API
    :param task_name: 任务名
    :return: API链接
    """
    api_url = ''
    disable = get_env(ENV_DISABLE_PROXY)
    if task_name and disable:
        items = disable.split('&')
        if task_name in items:
            log.info('当前任务已设置禁用代理')
            return api_url

    api_url = get_env(ENV_PROXY_API)
    if not api_url:
        log.info('暂未设置代理API，不进行代理')
    return api_url


def get_proxy(api_url: str, index: int = None) -> str:
    """
    提取代理IP
    :param api_url: API链接
    :param index: 索引
    :return:
    """
    if not api_url:
        return ''

    mark = f'【{index}】' if index else ''
    with lock:
        if len(proxies) <= 0:
            for try_num in range(MAX_RETRIES):
                try:
                    res = get_random_session().get(api_url)
                    ips = re.findall('(?:\d+\.){3}\d+:\d+', res.text)
                    if len(ips) < 1:
                        log.error(f'{mark}API代理提取失败，响应:{res.text}')
                        raise Exception('代理提取失败')
                    else:
                        [proxies.append(ip) for ip in ips]
                        break
                except:
                    if try_num < MAX_RETRIES - 1:
                        log.error(f'{mark}API代理提取失败，1秒后第{try_num + 1}次重试')
                        time.sleep(1)
                    else:
                        log.error(f'{mark}API代理提取失败，请检查余额或是否已添加白名单。')
    proxy = proxies.pop(0) if len(proxies) > 0 else None
    if proxy:
        log.info(f'{mark}当前代理: {proxy}')
    return proxy


class QLTask(metaclass=ABCMeta):
    def __init__(self, task_name: str, file_name: str, load_notice: bool = True):
        self.wait = 0
        self.success = 0
        self.fail_data = []
        self.task_name = task_name
        self.file_name = file_name
        self.un_auth = []
        if load_notice:
            log.info('==========公告==========')
            try:
                notice = get_random_session().get('https://static.xiaobooooo.com/text/notice').text
                log.info(f'\n{notice}')
            except:
                log.error('公告加载失败')
            log.info('==========公告==========\n')
        log.info('=====开始加载配置=====')
        self.lines = load_txt(self.file_name)
        self.total = len(self.lines)
        self.api_url = get_proxy_api(self.task_name)
        self.thread_num = get_thread_number(self.total)
        self.max_retries = get_max_retries()
        log.info('=====配置加载完毕=====\n')

    def run(self):
        log.info(f'=====开始运行任务=====')
        with futures.ThreadPoolExecutor(max_workers=self.thread_num) as pool:
            tasks = [pool.submit(self.main, index + 1, self.lines[index].strip()) for index in range(0, self.total)]
            futures.wait(tasks)
            for future in futures.as_completed(tasks):
                try:
                    if future.result():
                        self.success += 1
                except Exception as e:
                    log.error(f'任务执行失败: {repr(e)}')
        pool.shutdown()
        log.info(f'=====任务运行完毕=====\n')

        log.info('=====开始统计数据=====')
        self.statistics()
        log.info('=====数据统计完毕=====\n')

        log.info('=====开始保存文本=====')
        self.save()
        log.info('=====文本保存完毕=====\n')

        push_data = self.get_push_data()
        if push_data:
            log.info(f'=====开始推送消息=====')
            send(self.task_name, push_data)
            log.info(f'=====消息推送完毕=====\n')

    def main(self, index: int, text: str) -> bool:
        """
        主逻辑
        :param index: 索引
        :param text: 数据
        :return: 执行结果
        """
        log.info(f'【{index}】开始运行: {text.split("----")[0]}')
        proxy = get_proxy(self.api_url, index)
        for try_num in range(self.max_retries):
            try:
                self.task(index, text, proxy)
                return True
            except UnAuthorizationException:
                log.error(f'【{index}】{get_except(True)}')
                self.un_auth.append(text)
                return False
            except:
                if try_num < self.max_retries - 1:
                    log.error(f'【{index}】进行第{try_num + 1}次重试: {get_except()}')
                    proxy = get_proxy(self.api_url, index)
                else:
                    log.error(f'【{index}】重试完毕: {get_except()}')
                    self.fail_data.append(f'【{index}】{get_except()}')
        return False

    def statistics(self):
        """数据统计"""
        if self.fail_data:
            log_data = '-----失败数据统计-----\n'
            log_data += ''.join([f'{fail}\n' for fail in self.fail_data])
            log.info(log_data[:-1])

    def get_push_data(self) -> str:
        """
        推送数据
        :return: 推送数据
        """
        return f'总任务数：{self.total}\n成功数：{self.success} (其中时间未到数：{self.wait})\n失败数：{len(self.fail_data)}'

    def save(self):
        """保存数据"""

    @abstractmethod
    def task(self, index: int, text: str, proxy: str):
        """
        任务
        :param index: 索引
        :param text: 数据
        :param proxy: 代理
        :return: 任务执行结果
        """
