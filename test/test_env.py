from gui_tester.config import Config        # type: ignore
from gui_tester.env.env import Environment  # type: ignore

# This test fails because of logger import...
# I can't resolve it.

def test_get_components():
    config = Config("com.serwylo.lexica", "lexica.apk", "4LP", True, True)
    env = Environment("emulator-5554", config)
    print(env.get_components())

def test_is_out_of_app():
    config = Config("com.serwylo.lexica", "lexica.apk", "4LP", True, True)
    env = Environment("emulator-5554", config)
    env.is_out_of_app()