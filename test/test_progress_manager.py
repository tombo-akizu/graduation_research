import time

from gui_tester.config import Config    # type: ignore
from gui_tester import progress_manager # type: ignore

def test_progress_manager_hour():
    m = progress_manager.create_progress_manager(1. / 2880., None, Config(None, None, "4LP", True, True))
    while not m.test_is_over():
        m.update()
        time.sleep(0.01)

def test_progress_manager_episode():
    m = progress_manager.create_progress_manager(None, 10, Config(None, None, "4LP", True, True))
    while not m.test_is_over():
        m.update()
        time.sleep(0.01)