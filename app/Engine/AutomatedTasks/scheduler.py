from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from . import start_game, lynch, mafia_kill
from app.Engine.DB.db_api import GameApi
from datetime import timedelta

class GameScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="Europe/Berlin")
        self.scheduler.start()

    def create_game_start(self, game):
        trigger = DateTrigger(
            run_date=game.start_time
        )
        self.scheduler.add_job(func=start_game.do, args=[game.id], trigger=trigger)

    def get_jobs(self):
        jobs = self.scheduler.get_jobs()
        return jobs

    def _dummy_fun(self):
        print('dummy')
        return 1

    def create_dummy_job(self):
        self.scheduler.add_job(func=self._dummy_fun, trigger='cron', second=5)

    def app_start(self):
        game_api = GameApi()
        games = game_api.list_games()
        for game in games:
            # creating jobs for game start
            if game.status.name == 'waiting_for_start':
                self.create_game_start(game)
            # creating jobs for lynch and kill
            if game.status.name == 'in_progress':
                self.create_lynch_for_actual_day(game)
                self.create_mafia_kill_for_actual_day(game)

    def create_lynch_for_actual_day(self, game):
        day_duration = game.phases[0].phase_duration
        seconds = int(game.day_no) * day_duration
        trigger = DateTrigger(
            run_date=game.start_time + timedelta(seconds=seconds)
        )
        self.scheduler.add_job(func=lynch.do, args=[game.id], trigger=trigger)

    def create_mafia_kill_for_actual_day(self, game):
        day_duration = game.phases[0].phase_duration
        night_duration = game.phases[1].phase_duration
        seconds = int(game.day_no) * (day_duration + night_duration)
        trigger = DateTrigger(
            run_date=game.start_time + timedelta(seconds=seconds)
        )
        self.scheduler.add_job(func=mafia_kill.do, args=[game.id], trigger=trigger)

    def remove_jobs_for_game(self, game):
        jobs = self.get_jobs()
        for job in jobs:
            game_id = job.args[0]
            if game.id == game_id:
                job.remove()
