import gui_tester.config as config  # type: ignore

class RewardCalculator:
    def __init__(self):
        self.path_dict = {}

    def calc_singlenet(self, step_to_call_target: int, is_new_path: bool, reward_rising_rate: float):
        # step_to_call_target == -1 means target method wasn't called.
        if step_to_call_target == -1:
            return -0.001
        elif not is_new_path:
            return -0.001
        elif step_to_call_target == 0:
            return 1 * reward_rising_rate
        else:
            return 0.01 * (config.config.discount_rate ** step_to_call_target) * reward_rising_rate
        
def calc_explorer()