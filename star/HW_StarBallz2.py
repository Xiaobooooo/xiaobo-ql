"""
cron: 0 21 * * *
new Env('Star_Ballz_小号')
"""
from HW_StarFlappy2 import Task, FILE_NAME

TASK_NAME = 'Star_Ballz_小号'

if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'ballz').run()
