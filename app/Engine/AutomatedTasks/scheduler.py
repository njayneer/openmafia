from apscheduler.triggers.date import DateTrigger
import app.Engine.AutomatedTasks.Tasks as Tasks
from app.Engine.DB.db_api import GameApi, JobApi
from datetime import timedelta, datetime


class GameScheduler:
    def __init__(self):
        self.job_api = JobApi()

    def create_game_start(self, game):
        trigger = DateTrigger(
            run_date=game.start_time
        )
        self.job_api.add_job('start_game', game, game.start_time)

    def get_jobs(self):
        jobs = self.scheduler.get_jobs()
        return jobs

    def _dummy_fun(self):
        print('dummy')
        return 1

    def create_dummy_job(self):
        self.scheduler.add_job(func=self._dummy_fun, trigger='cron', second=5)

    def create_lynch_for_actual_day(self, game):
        day_duration = game.phases[0].phase_duration
        seconds = int(game.day_no) * day_duration
        trigger = DateTrigger(
            run_date=game.start_time + timedelta(seconds=seconds)
        )
        self.job_api.add_job('lynch', game, game.start_time + timedelta(seconds=seconds))

    def create_mafia_kill_for_actual_day(self, game):
        day_duration = game.phases[0].phase_duration
        night_duration = game.phases[1].phase_duration
        seconds = int(game.day_no) * (day_duration + night_duration)
        trigger = DateTrigger(
            run_date=game.start_time + timedelta(seconds=seconds)
        )
        self.job_api.add_job('mafia_kill', game, game.start_time + timedelta(seconds=seconds))

    def remove_jobs_for_game(self, game):
        jobs = self.job_api.list_jobs()
        for job in jobs:
            game_id = job.game_id
            if game.id == game_id:
                self.job_api.remove_job(job.id)

    def check_jobs_and_run(self, game_id):  # TODO: solve race condition in DB (new->in_progress)
        #self.job_api.lock_table()
        jobs = self.job_api.list_jobs_for_game(game_id)
        jobs_to_do = []
        for job in jobs:
            if job.status == 'new' and datetime.now() > job.trigger_time:
                self.job_api.update_job_status(job.id, 'in_progress')
                jobs_to_do.append(job)
        #self.job_api.unlock_table()
        for job in jobs_to_do:
            getattr(Tasks, job.job_name).__call__(job.game_id)
            self.job_api.update_job_status(job.id, 'done')
