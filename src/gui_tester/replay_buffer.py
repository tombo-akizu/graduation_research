from collections import deque
import random

import torch

from gui_tester.path import Path    # type: ignore

class TrainData():
    def __init__(self, target_method_id, state: tuple, action_idx, reward, new_state: tuple, path: Path):
        self.target_method_id = target_method_id
        self.state = state
        self.action_idx = action_idx
        self.reward = reward
        self.new_state = new_state
        self.path = path
        self.priority = 0

    def set_priority(self, agent, experience):
        self.priority = agent.calc_td_error(self, experience)

    def __eq__(self, other):
        if self.target_method_id != other.target_method_id: return False
        if self.state != other.state: return False
        if self.action_idx != other.action_idx: return False
        if self.new_state != other.new_state: return False
        if self.path != other.path: return False
        return True

class ReplayBuffer():
    def __init__(self, config):
        self.buffer = deque([], maxlen=config.replay_ratio)
        self.off_per = config.off_per

    def push(self, item: TrainData):
        if item in self.buffer:
            self.buffer.remove(item)
        self.buffer.append(item)    # If the deque overflows, the first item is removed.

    def sample(self, batch_size):
        if self.off_per:
            if len(self) < batch_size:
                return random.sample(self.buffer, len(self))   # list of sampled data
            else:
                return random.sample(self.buffer, batch_size)
        else:
            if len(self) < batch_size:
                batch_size = len(self)

            sum, roulette = self.__get_priority_sum_and_roulette()
            rand = torch.rand(batch_size) * sum
            rand = torch.sort(rand).values
            i = 0
            j = 0
            batch = []
            while i < batch_size:
                if rand[i] < roulette[j]:
                    batch.append(self.buffer[j])
                    i += 1
                else:
                    if j < len(roulette) - 1:
                        j += 1
                    else:
                        assert False

            return batch
        
    def reset_priority(self, agent, experience):
        for data in self.buffer:
            data.set_priority(agent, experience)

    def __get_priority_sum_and_roulette(self):
        epsilon = 0.001
        sum = 0
        roulette = []
        for data in self.buffer:
            sum += data.priority + epsilon
            if len(roulette) > 0:
                roulette.append(roulette[-1] + data.priority + epsilon)
            else:
                roulette.append(data.priority + epsilon)
        return sum, roulette
    
    def __len__(self):
        return len(self.buffer)