"""
cron: 30 59 1 * * *
new Env('Star_Puzzle2048')
"""
from HW_StarBallz import Task

TASK_NAME = 'Star_Puzzle2048'
FILE_NAME = 'StarNetworkGameTokenPuzzle2048.txt'

if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'puzzle_2048').run()
