"""
cron: 0 21 * * *
new Env('Star_Ballz_小号')
"""
from HW_StarFlappy2 import Task

TASK_NAME = 'Star_Ballz_小号'
FILE_NAME = 'StarNetworkBallzToken.txt'

if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'ballz').run()
