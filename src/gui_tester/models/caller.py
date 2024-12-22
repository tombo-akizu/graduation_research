import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.utils.rnn as rnn

import gui_tester.config as config  # type: ignore

class Caller(nn.Module):
    def __init__(self):
        super(Caller, self).__init__()

        layer_size = config.config.state_size + config.config.state_size

        self.lstm = nn.LSTM(config.config.state_size, config.config.state_size, num_layers=2, batch_first=True)

        # The input is a vector composed of state-vector, target-method, and path-vector.
        self.layer1 = nn.Linear(layer_size, layer_size)

        self.layer2 = nn.Linear(layer_size, layer_size)
        self.layer3 = nn.Linear(layer_size, config.config.max_action_num)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, state, path):
        out, h = self.lstm(path)

        if not isinstance(out, torch.Tensor):
            out, _ = rnn.pad_packed_sequence(out, batch_first=True, padding_value=-2)

        # dim=-1 merges tensor with last dimention.
        #   If called from select_action_greedily, merge tensor with dim=0.
        #   If called from optimize_model, merge tensor with dim=1.
        x = torch.cat((state, out[:, -1, :]), dim=-1)
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)