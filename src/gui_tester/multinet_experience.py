from __future__ import annotations
import random

from gui_tester.experience import Experience                # type: ignore
from gui_tester.caller_replay_buffer import CallerReplayBuffer      # type: ignore
from gui_tester.explorer_replay_buffer import ExplorerReplayBuffer  # type: ignore
import gui_tester.config as config                          # type: ignore
import logger

class MultiNetExperience(Experience):
    def __init__(self):
        super().__init__()
        
        # Dictionary of terminal path of explorer mode.
        #   Key is tuple expression of terminal path.
        #   Value is how many episodes the target method is called after the mode switches on the terminal path.
        self.terminal_path_dict = {}
        self.current_terminal_path = None
        self.is_caller_mode = False
        self.target_method_is_called = False        # Target method has been called in the episode or hasn't.
        self.target_method_has_been_called = False  # Target method has been called through the past episodes or hasn't.

        self.explore_terminal_epsilon = config.config.explorer_terminal_epsilon_start
        self.epsilon_step = (config.config.explorer_terminal_epsilon_start - config.config.explorer_terminal_epsilon_end) / config.config.explorer_terminal_episode_end

        self.caller_replay_buffer = CallerReplayBuffer()
        self.explorer_replay_buffer = ExplorerReplayBuffer()

    def start_new_episode(self):
        super().start_new_episode()
        self.is_caller_mode = False
        self.target_method_is_called = False
        self.explore_terminal_epsilon = max(self.explore_terminal_epsilon - self.epsilon_step, config.config.explorer_terminal_epsilon_end)

    def is_to_switch(self, step_num):
        if self.is_caller_mode: return False
        if not self.target_method_has_been_called: return False
        if step_num >= config.config.explore_step_num: return True
        if self.terminal_path_dict.get(self.current_path.get_path_sequence_tuple(), 0) > 0: return False
        return random.random() >= self.explore_terminal_epsilon

    def switch(self):
        self.current_terminal_path = self.current_path.get_path_sequence_tuple()
        self.is_caller_mode = True

    def check_target_is_called(self, called_methods: int):
        if self.is_caller_mode and ((called_methods & (1 << config.config.target_method_id)) > 0):
            if self.current_terminal_path in self.terminal_path_dict:
                self.terminal_path_dict[self.current_terminal_path] += 1
            else:
                self.terminal_path_dict[self.current_terminal_path] = 1
                logger.logger.info("New path is appended in paths.")
                logger.logger.info("Current paths len is {}.".format(len(self.terminal_path_dict)))
            self.target_method_is_called = True
    
    def is_episode_terminal(self):
        return self.is_caller_mode and self.target_method_is_called

    def append(self, state: State, action_idx: int, new_state: State, called_methods: int):
        super().append(state, action_idx, new_state, called_methods)
        if (called_methods & (1 << config.config.target_method_id)) > 0:
            self.target_method_has_been_called = True
    
    def create_train_data(self):
        assert len(self.experience[-1]) >= 2
        called_methods_bits = self.experience[-1][-1].called_methods

        if called_methods_bits == 0:
            for i in range(config.config.method_num):
                self.explorer_replay_buffer.create_and_append_data(
                    item=self.experience[-1][-1],
                    target_method_id=i, 
                    step_to_call_target=-1, 
                    is_new_path=None,    # Don't care because step_to_call_target == -1.
                )
        else:
            for i in range(config.config.method_num):
                if (called_methods_bits & (1 << i)) > 0:
                    is_new_path = not self.path_has_been_taken(i)
                    for step_idx, experience_item in enumerate(self.experience[-1][1:], start=1):   # enumerate starts from 1 because self.experience[-1][0].state == None.
                        self.explorer_replay_buffer.create_and_append_data(
                            item=experience_item,
                            target_method_id=i, 
                            # step_to_call_target=(len(self.experience[-1]) - 1 - step_idx),
                            step_to_call_target=self.__step_num_to_call_method(step_idx, i),
                            is_new_path=is_new_path,
                        )
        self.caller_replay_buffer.create_and_append_data(
            item=self.experience[-1][-1],
            step_to_call_global_target=self.__step_num_to_call_method(len(self.experience[-1]) - 1, config.config.target_method_id)
        )

    def create_keep_out_train_data(self):
        item = self.experience[-1][-1]
        self.explorer_replay_buffer.create_and_append_keep_out_data(config.config.target_method_id, item.state, item.action_idx, self.current_path.clone())
        self.caller_replay_buffer.create_and_append_keep_out_data(config.config.target_method_id, item.state, item.action_idx)

    def __step_num_to_call_method(self, departure, method_id):
        step_idx = departure
        step_num = 0
        method_bit = 1 << method_id
        while (self.experience[-1][step_idx].called_methods & method_bit) == 0:
            step_idx += 1
            step_num += 1
            if step_idx == len(self.experience[-1]):
                return -1
        return step_num
    
    def sample_batch(self) -> tuple(list(Tensor), list(Tensor)):    # type: ignore
        return (self.explorer_replay_buffer.sample(), self.caller_replay_buffer.sample())
