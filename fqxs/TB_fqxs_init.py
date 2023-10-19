"""
cron: 0 0 * * * *
new Env('FQXS_INIT')
"""
import json
import logging
import os
import time

logging.basicConfig(level=logging.INFO, datefmt="%H:%M:%S", format='%(asctime)s %(message)s')
log = logging.getLogger()

TOMATO_READ_JSON = 'tomato_read.json'


def load_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as load_f:
        load_dict = json.load(load_f)  # 将json读取
        return load_dict


def write_file(file_path, json_dic):
    try:
        with open(file_path, 'w+', encoding='utf-8') as f:
            json.dump(json_dic, f, indent=4, ensure_ascii=False)
        return 1
    except Exception:
        log.error('写入文件异常')
        return 0


def tomato_read_json_create(cookie_arr) -> int:
    if os.path.exists(TOMATO_READ_JSON):
        log.info(f'存在[{TOMATO_READ_JSON}]文件，进行删除')
        os.remove(TOMATO_READ_JSON)
    init_user_list = []
    for count in range(len(cookie_arr)):
        sleep_finished = None
        format_time = time.strftime('%m-%d %H:%M:%S')  # 获取当前时间
        current_time = time.strftime('%H:%M:%S')
        if '05:00:00' <= current_time <= '08:00:00':
            sleep_finished = 'end_sleep'
        elif '22:00:00' <= current_time <= '23:45:00':
            sleep_finished = 'start_sleep'
        elif '23:45:00' < current_time <= '23:59:59' or '00:00:00' <= current_time <= '04:59:59':
            sleep_finished = 'start_sleep'
        elif '08:00:00' < current_time < '22:00:00':
            sleep_finished = 'end_sleep'
        user_json = {
            "name": "none",
            "amount": 0,
            "time": format_time,
            "sign": 0,
            "lottery": 0,
            "prev_task_timeStamp": 0,
            "treasure_task_cnt": 0,
            "shopping_earn_money_cnt": 0,
            "browse_products_cnt": 0,
            "excitation_ad_cnt": 0,
            "next_readComic": 1,
            "daily_play_game_cnt": 0,
            "next_readNovel": 0.5,
            "next_listenNoval": 0.5,
            "meal_finished": -1,
            "sleep_finished": sleep_finished,
            "title": "none"
        }
        init_user_list.append(user_json)
    return write_file(TOMATO_READ_JSON, init_user_list)


def tomato_read_json_init() -> int:
    user_list = load_file(TOMATO_READ_JSON)
    new_user_list = []
    for user_data in user_list:
        name = user_data.get('name')
        sleep_finished = user_data.get('sleep_finished')
        next_open_treasure_box = user_data.get('next_open_treasure_box')
        title = user_data.get('title')
        format_time = time.strftime('%m-%d %H:%M:%S')  # 获取当前时间
        if next_open_treasure_box is None:
            next_open_treasure_box = 0
        temp = {
            "name": name,
            "amount": 0,
            "time": format_time,
            "sign": 0,
            "lottery": 0,
            "prev_task_timeStamp": 0,
            "treasure_task_cnt": 0,
            "shopping_earn_money_cnt": 15,
            "browse_products_cnt": 10,
            "excitation_ad_cnt": 10,
            "next_readComic": 1,
            "daily_play_game_cnt": 5,
            "next_readNovel": 0.5,
            "next_short_video": 0.5,
            "next_listenNoval": 0.5,
            "meal_finished": -1,
            "sleep_finished": sleep_finished,
            "excitation_ad_repeat_cnt": 96,
            "next_open_treasure_box": next_open_treasure_box,
            "title": title
        }
        new_user_list.append(temp)
    return write_file(TOMATO_READ_JSON, new_user_list)


if __name__ == '__main__':
    # if 'tomato_read' in os.environ:
    #     cookies = os.getenv('tomato_read')
    # else:
    #     print("变量[tomato_read]不存在,请设置[tomato_read]变量后运行")
    #     exit(-1)

    cookies_list = cookies.split('&http')
    log.info(f"环境变量读取到{len(cookies_list)}个账号")
    if tomato_read_json_create(cookies_list) == 1:
        log.info('tomato信息创建成功')
    if tomato_read_json_init() == 1:
        log.info('tomato信息初始化成功')
