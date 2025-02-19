import datetime
from tqdm import tqdm   # type: ignore

import gui_tester.config as config  # type: ignore

class ProgressManager():
    def __init__(self):
        self.episode = 0
        self.start_time = datetime.datetime.now()

    def update(self):
        self.episode += 1

    def get_episode(self):
        return self.episode
    
    def get_elapse_sec(self):
        return (datetime.datetime.now() - self.start_time).total_seconds()
    
class ProgressManagerHour(ProgressManager):
    def __init__(self, limit_hour):
        super().__init__()
        self.limit_sec = limit_hour * 3600
        self.elapse_sec = 0

    def update(self):
        super().update()
        self.elapse_sec = (datetime.datetime.now() - self.start_time).total_seconds()

        # To make tqdm 100%...
        if self.elapse_sec > self.limit_sec:
            self.elapse_sec = self.limit_sec

        with tqdm(total=self.limit_sec) as pbar:
            pbar.n = self.elapse_sec
            pbar.refresh()

    def test_is_over(self):
        return self.elapse_sec >= self.limit_sec

class ProgressManagerEpisode(ProgressManager):
    def __init__(self, limit_episode):
        super().__init__()
        self.limit_episode = limit_episode

    def update(self):
        super().update()
        with tqdm(total=self.limit_episode) as pbar:
            pbar.n = self.episode
            pbar.refresh()

    def test_is_over(self):
        return self.episode >= self.limit_episode

def create_progress_manager(limit_hour, limit_episode):
    assert((limit_hour == None) ^ (limit_episode == None))  # ^ is XOR operator.
    if limit_hour != None:
        return ProgressManagerHour(limit_hour)
    else:
        return ProgressManagerEpisode(limit_episode)
