"""
cron: 30 0 1-23/8 * * *
new Env('Star_加速抽奖_小号')
"""
from HW_StarDrawSpeed import Task

TASK_NAME = 'Star_加速抽奖_小号'
FILE_NAME = 'StarNetworkToken2.txt'

if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
