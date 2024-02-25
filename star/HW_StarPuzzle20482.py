"""
cron: 15 1 * * *
new Env('Star_Puzzle2048_小号')
"""
from star.HW_StarFlappy2 import Task

TASK_NAME = 'Star_Puzzle2048_小号'
FILE_NAME = 'StarNetworkPuzzle2048Token.txt'

if __name__ == '__main__':
    Task(TASK_NAME, FILE_NAME, 'puzzle_2048').run()
