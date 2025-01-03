from __future__ import annotations
from collections import deque
import random

import gui_tester.config as config  # type: ignore
from gui_tester.state import State  # type: ignore

class TrainData():
    def __init__(self, state: State, action_idx, caller_reward, new_state: State):
        self.state = state
        self.action_idx = action_idx
        self.reward = caller_reward
        self.new_state = new_state

    def is_the_same_key(self, other: TrainData):
        if self.state != other.state: return False
        if self.action_idx != other.action_idx: return False
        if self.new_state != other.new_state: return False
        return True
    
    # def __eq__(self, other):


class CallerReplayBuffer():
    def __init__(self):
        # Deque of TrainData.
        self.buffer = deque([], maxlen=config.config.replay_ratio)

    # Create TrainData and append it to self.buffer.
    #  step_to_call_target == -1 means target method wasn't called.
    def create_and_append_data(
            self,
            item: ExperienceItem,   # type: ignore
            step_to_call_global_target: int
            ):
        caller_reward = self.__calc_caller_reward(step_to_call_global_target, item)
        data = TrainData(item.state, item.action_idx, caller_reward, item.new_state)

        duplecated_data = None
        for old_data in self.buffer:
            if data.is_the_same_key(old_data):
                duplecated_data = old_data
                break
        if duplecated_data != None:
            if data.reward < duplecated_data.reward:
                data.reward = duplecated_data.reward
            self.buffer.remove(old_data)
        self.buffer.append(data)

        self.__push(data)
                
    def __calc_caller_reward(self, step_to_call_global_target, item: ExperienceItem):   # type: ignore
        # step_to_call_target == -1 means target method wasn't called.
        if step_to_call_global_target == 0:
            return 1
        elif item.state == item.new_state:
            return -1
        elif step_to_call_global_target == -1:
            return -0.001
        else:
            return 0.01 * (config.config.discount_rate ** step_to_call_global_target)

    def create_and_append_keep_out_data(self, target_method_id, state, action_idx):
        data = TrainData(target_method_id, state, action_idx, -1, state)
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