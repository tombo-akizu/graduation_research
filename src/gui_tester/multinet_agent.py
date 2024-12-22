import copy
import random
import sys

import torch
import torch.nn as nn
import torch.nn.utils.rnn as rnn
from torch.optim import RMSprop

from gui_tester.agent import Agent              # type: ignore
from gui_tester.models.caller   import Caller   # type: ignore
from gui_tester.models.explorer import Explorer # type: ignore
import gui_tester.config as config  # type: ignore
import logger                       # type: ignore

class MultiNetAgent(Agent):
    # Mode to explore new path.
    MODE_EXPLORER = 0
    # Mode to act to call the target method.
    MODE_CALLER = 1

    def __init__(self):
        super().__init__()
        if config.config.model == "Multi":
            self.explorer_policy_dqn = Explorer()
            self.caller_policy_dqn = Caller()
        else:
            assert False

        if not config.config.off_per:
            logger.logger.error("PER for MultiNetAgent hasn't been implemented yet... Please execute with --off_per option.")
            sys.exit(1)

        self.explorer_target_dqn = copy.deepcopy(self.explorer_policy_dqn)
        self.caller_target_dqn = copy.deepcopy(self.caller_policy_dqn)
        self.explorer_optim = RMSprop(self.explorer_policy_dqn.parameters(), lr=config.config.learning_rate)
        self.caller_optim = RMSprop(self.caller_policy_dqn.parameters(), lr=config.config.learning_rate)
        self.explorer_policy_dqn = self.explorer_policy_dqn.to(config.config.torch_device)
        self.explorer_target_dqn = self.explorer_target_dqn.to(config.config.torch_device)
        self.caller_policy_dqn = self.caller_policy_dqn.to(config.config.torch_device)
        self.caller_target_dqn = self.caller_target_dqn.to(config.config.torch_device)
        self.criterion = nn.MSELoss().to(config.config.torch_device)

        self.mode = MultiNetAgent.MODE_EXPLORER

    def reset_mode(self):
        self.mode = MultiNetAgent.MODE_EXPLORER

    def switch_mode(self):
        logger.logger.info("mode switched")
        self.mode = MultiNetAgent.MODE_CALLER

    def is_to_select_action_greedily(self):
        if self.mode == MultiNetAgent.MODE_EXPLORER:
            return random.random() >= self.epsilon
        elif self.mode == MultiNetAgent.MODE_CALLER:
            return True
        else:
            assert False, "Invalid mode"

    def select_action_greedily(self, components, state, _target_mathod_id, current_path):
        # Start processing input tensors for DQN...
        state_tensor = state.get_tensor().to(config.config.torch_device)
        path_tensor = current_path.get_path_sequence_tensor().to(config.config.torch_device)
        
        state_tensor = torch.unsqueeze(state_tensor, dim=0)   # forward of LSTM requires 3-dim tensor...
        path_tensor = torch.unsqueeze(path_tensor, dim=0)
        # ...End processing input tensors for DQN.

        if self.mode == MultiNetAgent.MODE_EXPLORER:
            policy_dqn = self.explorer_policy_dqn
        elif self.mode == MultiNetAgent.MODE_CALLER:
            policy_dqn = self.caller_policy_dqn
        else:
            assert False

        with torch.no_grad():
            q = policy_dqn(state_tensor, path_tensor)

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
        state_batch             = torch.stack([data.state.get_tensor() for data in batch]       ).to(config.config.torch_device)
        new_state_batch         = torch.stack([data.new_state.get_tensor() for data in batch]   ).to(config.config.torch_device)
        action_idx_batch        = torch.tensor([data.action_idx for data in batch]  , dtype=torch.int64     ).to(config.config.torch_device)
        explorer_reward_batch   = torch.tensor([data.explorer_reward    for data in batch], dtype=torch.float32 ).to(config.config.torch_device)
        caller_reward_batch     = torch.tensor([data.caller_reward      for data in batch], dtype=torch.float32 ).to(config.config.torch_device)

        path_list = [data.path.get_path_sequence_tensor() for data in batch]
        new_path_list = [data.path.clone().append(data.new_state).get_path_sequence_tensor() for data in batch]
        path_batch = rnn.pad_sequence(path_list, batch_first=True, padding_value=-2).to(config.config.torch_device)
        new_path_batch = rnn.pad_sequence(new_path_list, batch_first=True, padding_value=-2).to(config.config.torch_device)
        path_lengths = (path_batch != -2).any(dim=2).sum(dim=1)
        new_path_lengths = (new_path_batch != -2).any(dim=2).sum(dim=1)

        path_batch = rnn.pack_padded_sequence(path_batch, path_lengths.cpu(), batch_first=True, enforce_sorted=False)
        new_path_batch = rnn.pack_padded_sequence(new_path_batch, new_path_lengths.cpu(), batch_first=True, enforce_sorted=False)
        # ...End processing input tensors for DQN.

        # Optimize each model.
        self.loss   = self.__optimize_each_mode_model(MultiNetAgent.MODE_EXPLORER, state_batch, new_state_batch, action_idx_batch, explorer_reward_batch, path_batch, new_path_batch)
        _           = self.__optimize_each_mode_model(MultiNetAgent.MODE_CALLER, state_batch, new_state_batch, action_idx_batch, caller_reward_batch, path_batch, new_path_batch)

    def __optimize_each_mode_model(self, mode, state_batch, new_state_batch, action_idx_batch, reward_batch, path_batch, new_path_batch):
        if mode == MultiNetAgent.MODE_EXPLORER:
            policy_dqn = self.explorer_policy_dqn
            target_dqn = self.explorer_target_dqn
            optim = self.explorer_optim
        elif mode == MultiNetAgent.MODE_CALLER:
            policy_dqn = self.caller_policy_dqn
            target_dqn = self.caller_target_dqn
            optim = self.caller_optim
        else:
            assert False

        state_action_values = policy_dqn(state_batch, path_batch).gather(dim=1, index=action_idx_batch.unsqueeze(1)).squeeze()

        # Compute argmax_a Q(s_t+1, a).
        argmax_action = torch.argmax(policy_dqn(new_state_batch, new_path_batch), dim=-1)

        # Collect Q'(s_t+1, argmax_a Q(s_t+1, a))
        with torch.no_grad():
            target_q = target_dqn(new_state_batch, new_path_batch)
            if not config.config.off_unactionable_flooring:
                for i, new_state_t in enumerate(new_state_batch):
                    mask = torch.ones(config.config.state_size, dtype=torch.bool).to(config.config.torch_device)
                    mask[new_state_t[1:] > 0] = False
                    target_q[i, mask] = torch.min(target_q[i,:]).item()
            
            selected_action_indices = target_q.gather(dim=1, index=argmax_action.unsqueeze(1)).squeeze()

        expected_state_action_values = reward_batch + config.config.discount_rate * selected_action_indices

        if state_action_values.dim() == 0:
            state_action_values = state_action_values.unsqueeze(0)

        # Compute loss
        loss = self.criterion(state_action_values, expected_state_action_values)

        # Optimize the model
        optim.zero_grad()
        loss.backward()

        # In-place gradient clipping
        torch.nn.utils.clip_grad_value_(policy_dqn.parameters(), 100)

        optim.step()
        return loss.item()

    def update_target_network(self):
        self.__update_each_mode_target_network(MultiNetAgent.MODE_EXPLORER)
        self.__update_each_mode_target_network(MultiNetAgent.MODE_CALLER)

    def __update_each_mode_target_network(self, mode):
        if mode == MultiNetAgent.MODE_EXPLORER:
            policy_dqn = self.explorer_policy_dqn
            target_dqn = self.explorer_target_dqn
        elif mode == MultiNetAgent.MODE_CALLER:
            policy_dqn = self.caller_policy_dqn
            target_dqn = self.caller_target_dqn
        else:
            assert False

        target_net_state_dict = target_dqn.state_dict()
        policy_net_state_dict = policy_dqn.state_dict()
        for key in policy_net_state_dict:
            target_net_state_dict[key] = policy_net_state_dict[key] * config.config.soft_update_rate + target_net_state_dict[key] * (1 - config.config.soft_update_rate)
        target_dqn.load_state_dict(target_net_state_dict)