from flask import flash
from functools import wraps
from app.Engine.AutomatedTasks.scheduler import GameScheduler

def handle_jobs(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        game_id = kwargs['game_id']
        game_scheduler = GameScheduler()
        game_scheduler.check_jobs_and_run(game_id)

        return f(*args, **kwargs)
    return decorated_function
