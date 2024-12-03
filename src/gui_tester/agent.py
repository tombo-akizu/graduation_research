# It is required to import them the first.
import torch
import intel_extension_for_pytorch as ipex
import torch.nn as nn
import torch.nn.utils.rnn as rnn
from torch.optim import RMSprop

import copy
import random

from gui_tester.models.four_lp import FourLP
from gui_tester.models.four_lp_with_path import FourLPWithPath
from gui_tester.models.lstm import LSTM
from gui_tester.path import Path
import logger

class Agent():
    def __init__(self, config):
        self.config = config

        self.epsilon = 0
        self.epsilon_step = (config.epsilon_start - config.epsilon_end) / config.epsilon_episode_end

        # Dictionary whose key is component group and whose value is its ID.
        # Components with the same resource-id and actionabilities are in the same component group.
        self.component_group_dict = {}

        # Switch model with config.model
        if config.model == "4LP":
            self.policy_dqn = FourLP(config)
        elif config.model == "4LPWithPath":
            self.policy_dqn = FourLPWithPath(config)
        elif config.model == "LSTM":
            self.policy_dqn = LSTM(config)
        else:
            assert False

        self.target_dqn = copy.deepcopy(self.policy_dqn)
        self.optim = RMSprop(self.policy_dqn.parameters(), lr=config.learning_rate)

        self.policy_dqn = self.policy_dqn.to("cpu")
        self.target_dqn = self.target_dqn.to("cpu")
        self.criterion = nn.MSELoss().to("cpu")
        # self.policy_dqn, self.optim = ipex.optimize(self.policy_dqn, optimizer=self.optim)

        # Loss value cache.
        self.loss = 0

    # Update epsilon of the epsilon-greedy method.
    def update_epsilon(self, current_episode):
        if current_episode < self.config.epsilon_episode_end:
            self.epsilon = self.config.epsilon_start - self.epsilon_step * current_episode

    # Update self.component_group_dict with the current components.
    # If there is a component whose component_group hasn't recorded yet in self.component_group_dict, record it.
    def update_component_group_dict(self, components):
        for component in components:
            key = component.get_group_key()
            if not key in self.component_group_dict:
                idx = len(self.component_group_dict)
                self.component_group_dict[key] = idx
        assert len(self.component_group_dict) <= self.config.state_size

    # Get state-embedding vector.
    # Each item of state-embedding vector is count of GUI components in a component group.
    # Call after update_component_group_dict.
    def get_state(self, components):
        state = [0] * self.config.state_size
        for component in components:
            key = component.get_group_key()
            assert key in self.component_group_dict
            idx = self.component_group_dict[key]
            state[idx] += 1
        return tuple(state)
    
    def select_action_randomly(self, components):
        return random.choice(components)
    
    def select_action_greedily(self, components, state, target_mathod_id, experience):
        state = torch.tensor((target_mathod_id,) + state, dtype=torch.float32).to("cpu")

        if self.config.model == "4LP" or self.config.model == "4LPWithPath":
            path_tensor = experience.get_current_path().get_tensor(self.config).to("cpu")
        elif self.config.model == "LSTM":
            path_tensor = experience.get_current_path().get_path_sequence_tensor(experience, self.config).to("cpu")
        
        state = torch.unsqueeze(state, dim=0)   # forward of LSTM requires 3-dim tensor...
        path_tensor = torch.unsqueeze(path_tensor, dim=0)

        with torch.no_grad():
            q = self.policy_dqn(state, path_tensor)

        q = torch.squeeze(q, dim=0)

        actionable_group_ids = list({self.component_group_dict[component.get_group_key()] for component in components})

        assert len(actionable_group_ids) > 0

        mask = torch.ones(q.shape[0], dtype=torch.bool).to("cpu")
        mask[actionable_group_ids] = False
        q[mask] = -float("inf")

        max_index = torch.argmax(q).item()

        components_with_max_q_value = [component for component in components if self.component_group_dict[component.get_group_key()] == max_index]
        return random.choice(components_with_max_q_value)
    
    def get_component_group_idx(self, component):
        return self.component_group_dict[component.get_group_key()]
    
    def optimize_model(self, experience):
        batch = experience.replay_buffer.sample(self.config.batch_size)

        if len(batch) == 0:
            logger.logger.info("empty batch")
            return
        
        target_method_id_batch  = torch.tensor([data.target_method_id for data in batch]                            ).to("cpu")
        state_batch             = torch.tensor([data.state for data in  batch]              , dtype=torch.float32   ).to("cpu")
        action_idx_batch        = torch.tensor([data.action_idx for data in batch]          , dtype=torch.int64     ).to("cpu")
        reward_batch            = torch.tensor([data.reward for data in batch]              , dtype=torch.float32   ).to("cpu")
        new_state_batch         = torch.tensor([data.new_state for data in batch]           , dtype=torch.float32   ).to("cpu")

        state_batch = torch.cat((target_method_id_batch.unsqueeze(1), state_batch), dim=1)
        new_state_batch = torch.cat((target_method_id_batch.unsqueeze(1), new_state_batch), dim=1)

        if self.config.model == "4LP" or self.config.model == "4LPWithPath":
            path_list = [data.path.get_tensor(self.config) for data in batch]
            new_path_list = [data.path.clone().append(experience.get_state_id(data.new_state)).get_tensor(self.config) for data in batch]
            path_batch = torch.stack(path_list).to("cpu")
            new_path_batch = torch.stack(new_path_list).to("cpu")
        elif self.config.model == "LSTM":
            path_list = [data.path.get_path_sequence_tensor(experience, self.config) for data in batch]
            new_path_list = [data.path.clone().append(experience.get_state_id(data.new_state)).get_path_sequence_tensor(experience, self.config) for data in batch]
            path_batch = rnn.pad_sequence(path_list, batch_first=True, padding_value=-2).to("cpu")
            new_path_batch = rnn.pad_sequence(new_path_list, batch_first=True, padding_value=-2).to("cpu")
        else:
            assert False

        state_action_values = self.policy_dqn(state_batch, path_batch).gather(dim=1, index=action_idx_batch.unsqueeze(1)).squeeze()

        # Compute argmax_a Q(s_t+1, a).
        argmax_action = torch.argmax(self.policy_dqn(new_state_batch, new_path_batch), dim=-1)

        # Collect Q'(s_t+1, argmax_a Q(s_t+1, a))
        with torch.no_grad():
            target_q = self.target_dqn(new_state_batch, new_path_batch).gather(dim=1, index=argmax_action.unsqueeze(1)).squeeze()

        expected_state_action_values = reward_batch + self.config.discount_rate * target_q

        # Compute loss
        loss = self.criterion(state_action_values, expected_state_action_values)

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
            target_net_state_dict[key] = policy_net_state_dict[key] * self.config.soft_update_rate + target_net_state_dict[key] * (1 - self.config.soft_update_rate)
        self.target_dqn.load_state_dict(target_net_state_dict)

    def get_loss(self):
        return self.loss