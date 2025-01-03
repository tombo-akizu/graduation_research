from __future__ import annotations
from collections import deque
import random

import gui_tester.config as config  # type: ignore
from gui_tester.path import Path    # type: ignore
from gui_tester.state import State  # type: ignore

class TrainData():
    def __init__(self, target_method_id, state: State, action_idx, explorer_reward, new_state: State, path: Path):
        self.target_method_id = target_method_id
        self.state = state
        self.action_idx = action_idx
        self.reward = explorer_reward
        self.new_state = new_state
        self.path = path

class ExplorerReplayBuffer():
    def __init__(self):
        # Deque of TrainData.
        self.buffer = deque([], maxlen=config.config.replay_ratio)

    # Create TrainData and append it to self.buffer.
    #  step_to_call_target == -1 means target method wasn't called.
    def create_and_append_data(
            self,
            item: ExperienceItem,   # type: ignore
            target_method_id: int, 
            step_to_call_target: int, 
            is_new_path: bool,
            ):
        explorer_reward = self.__calc_explorer_reward(step_to_call_target, is_new_path)
        data = TrainData(target_method_id, item.state, item.action_idx, explorer_reward, item.new_state, item.path)
        self.__push(data)
        
    def __calc_explorer_reward(self, step_to_call_target: int, is_new_path: bool):
        # step_to_call_target == -1 means target method wasn't called.
        if step_to_call_target == -1:
            return -0.001
        elif not is_new_path:
            return -0.001
        elif step_to_call_target == 0:
            return 1
        else:
            return 0.01 * (config.config.discount_rate ** step_to_call_target)
        
    def create_and_append_keep_out_data(self, target_method_id, state, action_idx, path):
        data = TrainData(target_method_id, state, action_idx, -1, state, path)
        self.__push(data)

    def __push(self, item: TrainData):
        self.buffer.append(item)    # If the deque overflows, the first item is removed.

    def sample(self):
        if len(self) < config.config.batch_size:
            return random.sample(self.buffer, len(self))   # list of sampled data
        else:
            return random.sample(self.buffer, config.config.batch_size)
            
    def __len__(self):
        return len(self.buffer)