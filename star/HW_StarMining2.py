"""
cron: 0 0-23/8 * * *
new Env('Star_挖矿_小号')
"""
from HW_StarMining import Task

TASK_NAME = 'Star_挖矿_小号'
FILE_NAME = 'StarNetworkToken2.txt'


if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME).run()
