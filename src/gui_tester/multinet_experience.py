from __future__ import annotations
import random

from gui_tester.experience import Experience                # type: ignore
from gui_tester.multinet_replay_buffer import ReplayBuffer  # type: ignore
import gui_tester.config as config                          # type: ignore

class MultiNetExperience(Experience):
    def __init__(self):
        super().__init__()
        
        # Dictionary of terminal path of explorer mode.
        #   Key is tuple expression of terminal path.
        #   Value is how many episodes the target method is called after the mode switches on the terminal path.
        self.terminal_path_dict = {}
        self.current_terminal_path = None
        self.is_caller_mode = False
        self.target_method_is_called = False

        self.explore_terminal_epsilon = config.config.explorer_terminal_epsilon_start
        self.epsilon_step = (config.config.explorer_terminal_epsilon_start - config.config.explorer_terminal_epsilon_end) / config.config.explorer_terminal_episode_end

        # Overwrite.
        self.replay_buffer = ReplayBuffer()

    def start_new_episode(self):
        super().start_new_episode()
        self.is_caller_mode = False
        self.target_method_is_called = False
        self.explore_terminal_epsilon = max(self.explore_terminal_epsilon - self.epsilon_step, config.config.explorer_terminal_episode_end)

    def is_to_switch(self, step_num):
        if self.is_caller_mode: return False
        if self.current_path == None: return False
        if step_num >= config.config.explore_step_num: return True
        if self.terminal_path_dict.get(self.current_path.get_path_sequence_tuple(), 0) > 3: return False
        return random.random() >= self.explore_terminal_epsilon

    def switch(self):
        self.current_terminal_path = self.current_path.get_path_sequence_tuple()
        self.is_caller_mode = True

    def check_target_is_called(self, called_methods: int, target_method_id: int):
        if self.is_caller_mode and ((called_methods & (1 << target_method_id)) > 0):
            if self.current_terminal_path in self.terminal_path_dict:
                self.terminal_path_dict[self.current_terminal_path] += 1
            else:
                self.terminal_path_dict[self.current_terminal_path] = 1
            self.target_method_is_called = True
        print("current paths len is {}".format(len(self.terminal_path_dict)))
    
    def is_episode_terminal(self):
        return self.is_caller_mode and self.target_method_is_called
    
    # Override Experience.create_train_data.
    def create_train_data(self, target_method_id):
        assert len(self.experience[-1]) >= 2
        called_methods_bits = self.experience[-1][-1].called_methods

        if (called_methods_bits & (1 << target_method_id)) > 0:
            for step_idx, experience_item in enumerate(self.experience[-1][1:], start=1):   # enumerate starts from 1 because self.experience[-1][0].state == None.
                self.replay_buffer.create_and_append_data(
                    item=experience_item,
                    target_method_id=target_method_id,
                    step_to_call_target=self.__step_num_to_call_method(step_idx, target_method_id),
                    terminal_path_dict=self.terminal_path_dict
                )
        else:
            for experience_item in self.experience[-1][1:]:
                self.replay_buffer.create_and_append_data(
                    item=experience_item,
                    target_method_id=target_method_id,
                    step_to_call_target=-1,
                    terminal_path_dict=self.terminal_path_dict
                )

    def __step_num_to_call_method(self, departure, method_id):
        step_idx = departure
        step_num = 0
        method_bit = 1 << method_id
        while (self.experience[-1][step_idx].called_methods & method_bit) == 0:
            step_idx += 1
            step_num += 1
        return step_num