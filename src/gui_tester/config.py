import pickle
import re
import subprocess

import torch

from instrument_data import InstrumentData  # type: ignore

class Config():
    def __init__(self, package, apk_path, model, off_reward_rising, off_per, off_unactionable_flooring):
        self.package = package
        self.apk_path = apk_path
        self.install_timeout = 20

        self.epsilon_start = 1.0
        self.epsilon_end = 0.1
        self.epsilon_episode_end = 50

        result = subprocess.run(['adb', 'shell', 'wm', 'size'], capture_output=True, text=True).stdout
        re_result = re.search(r'.*?(\d+)x(\d+).*?', result)
        self.emulator_screen_width = int(re_result.group(1))
        self.emulator_screen_height = int(re_result.group(2))

        self.state_size = 500

        self.max_state_repeat = 10
        self.max_ep_length = 20

        # How many times the gui_tester calculate coverage (max).
        self.coverage_frequency = 100

        # Length of replay buffer.
        self.replay_ratio = 10000

        self.discount_rate = 0.5
        self.soft_update_rate = 0.1   # tau

        self.max_action_num = 500
        self.learning_rate = 0.00025

        self.batch_size = 32

        self.max_try_time_to_empty_screen = 10

        self.max_uiautomator_retry = 10

        instrument_data = pickle.load(open("instrument_data/instrument.pkl", "rb"))
        self.method_num = len(instrument_data)

        self.model = model

        self.off_reward_rising = off_reward_rising
        self.reward_rise_rate = 1.0 / 900.0 # About 900 steps are taken in an hour.
        self.off_per = off_per
        self.off_unactionable_flooring = off_unactionable_flooring

        if torch.cuda.is_available():
            self.torch_device = "cuda"
        elif torch.backends.mps.is_available():
            self.torch_device = "mps"
        else:
            self.torch_device = "cpu"