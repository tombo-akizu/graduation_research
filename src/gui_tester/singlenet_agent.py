import copy
import random

import torch
import torch.nn as nn
import torch.nn.utils.rnn as rnn
from torch.optim import RMSprop

from gui_tester.agent import Agent                              # type: ignore
from gui_tester.models.four_lp import FourLP                    # type: ignore
from gui_tester.models.four_lp_with_path import FourLPWithPath  # type: ignore
from gui_tester.models.lstm import LSTM                         # type: ignore
from gui_tester.replay_buffer import TrainData                  # type: ignore
import gui_tester.config as config  # type: ignore
import logger                       # type: ignore

class SingleNetAgent(Agent):
    def __init__(self):
        super().__init__()

        # Switch model with config.model
        if config.config.model == "4LP":
            self.policy_dqn = FourLP()
        elif config.config.model == "4LPWithPath":
            self.policy_dqn = FourLPWithPath()
        elif config.config.model == "LSTM":
            self.policy_dqn = LSTM()
        else:
            assert False

        self.target_dqn = copy.deepcopy(self.policy_dqn)
        self.optim = RMSprop(self.policy_dqn.parameters(), lr=config.config.learning_rate)

        self.policy_dqn = self.policy_dqn.to(config.config.torch_device)
        self.target_dqn = self.target_dqn.to(config.config.torch_device)

        if config.config.off_per:
            self.criterion = nn.MSELoss().to(config.config.torch_device)
        else:
            self.criterion = nn.MSELoss(reduction="none").to(config.config.torch_device)

    def is_to_select_action_greedily(self):
        return random.random() >= self.epsilon

    def select_action_greedily(self, components, state, current_path):
        # Start processing input tensors for DQN...
        target_mathod_id_tensor = torch.tensor([config.config.target_mathod_id], dtype=torch.float32)
        input = torch.cat((target_mathod_id_tensor, state.get_tensor())).to(config.config.torch_device)

        if config.config.model == "4LP" or config.config.model == "4LPWithPath":
            path_tensor = current_path.get_tensor().to(config.config.torch_device)
        elif config.config.model == "LSTM":
            path_tensor = current_path.get_path_sequence_tensor().to(config.config.torch_device)
        
        input = torch.unsqueeze(input, dim=0)   # forward of LSTM requires 3-dim tensor...
        path_tensor = torch.unsqueeze(path_tensor, dim=0)
        # ...End processing input tensors for DQN.

        with torch.no_grad():
            q = self.policy_dqn(input, path_tensor)

        q = torch.squeeze(q, dim=0)

        actionable_group_ids = [component.id for component in components]

        assert len(actionable_group_ids) > 0

        mask = torch.ones(q.shape[0], dtype=torch.bool).to(config.config.torch_device)
        mask[actionable_group_ids] = False
        q[mask] = -float("inf")

        max_index = torch.argmax(q).item()

        components_with_max_q_value = [component for component in components if component.id == max_index]
        return random.choice(components_with_max_q_value)
        
    def optimize_model(self, batch):
        if len(batch) == 0:
            logger.logger.info("empty batch")
            return
        
        # Start processing input tensors for DQN...
        action_idx_batch    = torch.tensor([data.action_idx for data in batch]  , dtype=torch.int64     ).to(config.config.torch_device)
        reward_batch        = torch.tensor([data.reward for data in batch]      , dtype=torch.float32   ).to(config.config.torch_device)
        priority_batch      = torch.tensor([data.priority for data in batch]    , dtype=torch.float32   ).to(config.config.torch_device)

        state_list = []
        new_state_list = []
        for data in batch:
            target_method_id_tensor = torch.tensor([data.target_method_id], dtype=torch.float32)
            state_list.append(torch.cat((target_method_id_tensor, data.state.get_tensor())))
            new_state_list.append(torch.cat((target_method_id_tensor, data.new_state.get_tensor())))
        state_batch     = torch.stack(state_list)       .to(config.config.torch_device)
        new_state_batch = torch.stack(new_state_list)   .to(config.config.torch_device)

        priority_weight_batch = torch.reciprocal(priority_batch)

        if config.config.model == "4LP" or config.config.model == "4LPWithPath":
            path_list = [data.path.get_tensor() for data in batch]
            new_path_list = [data.path.clone().append(data.new_state).get_tensor() for data in batch]
            path_batch = torch.stack(path_list).to(config.config.torch_device)
            new_path_batch = torch.stack(new_path_list).to(config.config.torch_device)
        elif config.config.model == "LSTM":
            path_list = [data.path.get_path_sequence_tensor() for data in batch]
            new_path_list = [data.path.clone().append(data.new_state).get_path_sequence_tensor() for data in batch]
            path_batch = rnn.pad_sequence(path_list, batch_first=True, padding_value=-2).to(config.config.torch_device)
            new_path_batch = rnn.pad_sequence(new_path_list, batch_first=True, padding_value=-2).to(config.config.torch_device)
            path_lengths = (path_batch != -2).any(dim=2).sum(dim=1)
            new_path_lengths = (new_path_batch != -2).any(dim=2).sum(dim=1)

            path_batch = rnn.pack_padded_sequence(path_batch, path_lengths.cpu(), batch_first=True, enforce_sorted=False)
            new_path_batch = rnn.pack_padded_sequence(new_path_batch, new_path_lengths.cpu(), batch_first=True, enforce_sorted=False)
        else:
            assert False
        # ...End processing input tensors for DQN.

        state_action_values = self.policy_dqn(state_batch, path_batch).gather(dim=1, index=action_idx_batch.unsqueeze(1)).squeeze()

        # Compute argmax_a Q(s_t+1, a).
        argmax_action = torch.argmax(self.policy_dqn(new_state_batch, new_path_batch), dim=-1)

        # Collect Q'(s_t+1, argmax_a Q(s_t+1, a))
        with torch.no_grad():
            target_q = self.target_dqn(new_state_batch, new_path_batch)
            if not config.config.off_unactionable_flooring:
                for i, new_state_t in enumerate(new_state_batch):
                    mask = torch.ones(config.config.state_size, dtype=torch.bool).to(config.config.torch_device)
                    mask[new_state_t[1:] > 0] = False
                    target_q[i, mask] = torch.min(target_q[i,:]).item()
            
            selected_action_indices = target_q.gather(dim=1, index=argmax_action.unsqueeze(1)).squeeze()

        expected_state_action_values = reward_batch + config.config.discount_rate * selected_action_indices

        # Compute loss
        if config.config.off_per:
            loss = self.criterion(state_action_values, expected_state_action_values)
        else:
            loss = self.criterion(state_action_values, expected_state_action_values)
            loss = (loss * priority_weight_batch).mean()

        self.loss = loss.item()

        # Optimize the model
        self.optim.zero_grad()
        loss.backward()

        # In-place gradient clipping
        torch.nn.utils.clip_grad_value_(self.policy_dqn.parameters(), 100)

        self.optim.step()

    def update_target_network(self):
        target_net_state_dict = self.target_dqn.state_dict()
        policy_net_state_dict = self.policy_dqn.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key] * config.config.soft_update_rate + target_net_state_dict[key] * (1 - config.config.soft_update_rate)
        self.target_dqn.load_state_dict(target_net_state_dict)

    def calc_td_error(self, train_data: TrainData):
        # Start processing input tensors for DQN...
        target_method_id_tensor = torch.tensor([train_data.target_method_id], dtype=torch.float32)
        state = torch.cat((target_method_id_tensor, train_data.state.get_tensor())).to(config.config.torch_device)
        new_state = torch.cat((target_method_id_tensor, train_data.new_state.get_tensor())).to(config.config.torch_device)

        new_path = train_data.path.clone().append(train_data.new_state)

        if config.config.model == "4LP" or config.config.model == "4LPWithPath":
            path_tensor = train_data.path.get_tensor().to(config.config.torch_device)
            new_path_tensor = new_path.get_tensor().to(config.config.torch_device)
        elif config.config.model == "LSTM":
            path_tensor = train_data.path.get_path_sequence_tensor().to(config.config.torch_device)
            new_path_tensor = new_path.get_path_sequence_tensor().to(config.config.torch_device)
        else:
            assert False

        state = torch.unsqueeze(state, dim=0)   # forward of LSTM requires 3-dim tensor...
        new_state = torch.unsqueeze(new_state, dim=0)
        path_tensor = torch.unsqueeze(path_tensor, dim=0)
        new_path_tensor = torch.unsqueeze(new_path_tensor, dim=0)
        # ...End processing input tensors for DQN.

        with torch.no_grad():
            target_q = self.target_dqn(new_state, new_path_tensor)

            mask = torch.ones(config.config.state_size, dtype=torch.bool).to(config.config.torch_device)
            mask[new_state[0, 1:] > 0] = False
            target_q[:, mask] = -float("inf")
            target = torch.max(target_q, dim=1).values.item()
            
            predict = self.policy_dqn(state, path_tensor)[0, train_data.action_idx]

        td_error = abs(train_data.reward + target - predict).item()
        return td_error