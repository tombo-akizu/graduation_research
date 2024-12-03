import torch
import torch.nn as nn
import torch.nn.functional as F

class FourLPWithPath(nn.Module):

    def __init__(self, config):
        super(FourLPWithPath, self).__init__()

        layer_size = config.state_size + 1 + config.state_size + 1

        # The input is a vector composed of state-vector, target-method, path-vector, and has_taken_out_of_app.
        self.layer1 = nn.Linear(layer_size, layer_size)

        self.layer2 = nn.Linear(layer_size, layer_size)
        self.layer3 = nn.Linear(layer_size, config.max_action_num)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, state, path):
        # dim=-1 merges tensor with last dimention.
        #   If called from select_action_greedily, merge tensor with dim=0.
        #   If called from optimize_model, merge tensor with dim=1.
        x = torch.cat((state, path), dim=-1)
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)