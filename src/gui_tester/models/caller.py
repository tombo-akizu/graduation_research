import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.utils.rnn as rnn

import gui_tester.config as config  # type: ignore

class Caller(nn.Module):
    def __init__(self):
        super(Caller, self).__init__()

        layer_size = config.config.state_size

        # The input is a vector composed of state-vector, target-method, and path-vector.
        self.layer1 = nn.Linear(layer_size, layer_size)

        self.layer2 = nn.Linear(layer_size, layer_size)
        self.layer3 = nn.Linear(layer_size, config.config.max_action_num)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, state, _path, _target):
        x = F.relu(self.layer1(state))
        x = F.relu(self.layer2(x))
        return self.layer3(x)