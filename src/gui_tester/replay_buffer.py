from collections import deque
import random

from gui_tester.path import Path

class TrainData():
    def __init__(self, target_method_id, state: tuple, action_idx, reward, new_state: tuple, path: Path):
        self.target_method_id = target_method_id
        self.state = state
        self.action_idx = action_idx
        self.reward = reward
        self.new_state = new_state
        self.path = path

class ReplayBuffer():
    def __init__(self, config):
        self.buffer = deque([], maxlen=config.replay_ratio)

    def push(self, item: TrainData):
        self.buffer.append(item)    # If the deque overflows, the first item is removed.

    def sample(self, batch_size):
        if len(self) < batch_size:
            return random.sample(self.buffer, len(self))   # list of sampled data
        else:
            return random.sample(self.buffer, batch_size)
    
    def __len__(self):
        return len(self.buffer)