"""
cron: 30 59 1 * * *
new Env('Star_Puzzle2048')
"""
from HW_StarBallz import Task
from HW_StarFlappy import FILE_NAME

TASK_NAME = 'Star_Puzzle2048'

if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'puzzle_2048').run()
