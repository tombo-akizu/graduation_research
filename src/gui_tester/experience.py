from gui_tester.path import Path                    # type: ignore
from gui_tester.replay_buffer import ReplayBuffer   # type: ignore
from gui_tester.state import State                  # type: ignore
import gui_tester.config as config  # type: ignore

class ExperienceItem():
    def __init__(self, state: State, action_idx: int, new_state: State, called_methods: int, path: Path):
        self.state = state
        self.action_idx = action_idx
        self.new_state = new_state
        self.called_methods = called_methods
        self.path = path

# Experience manages the following data.
# - Experience in reinforcement learning context:   experience
# - Traning data created from experience:           replay_buffer
# - How many times the same state repeats:          state_repeat_counter
# - Path of current episode:                        current_path
class Experience():
    def __init__(self):
        # 2-dimentional list. Each item is list[ExperienceItem] of an episode.
        self.experience = []
        self.replay_buffer = ReplayBuffer()
        self.state_repeat_counter = 0
        self.current_path = Path()

    def start_new_episode(self):
        self.experience.append([])
        self.state_repeat_counter = 0
        self.current_path = Path()

    def append(self, state: State, action_idx: int, new_state: State, called_methods: int):
        self.current_path.append(new_state)
        self.experience[-1].append(ExperienceItem(state, action_idx, new_state, called_methods, self.current_path.clone()))
        if (state != None) and (state == new_state):    # On the first step of the episode, state == None.
            self.state_repeat_counter += 1
        else:
            self.state_repeat_counter = 0

    def append_out_of_app(self):
        self.current_path.append_out_of_app()

    def state_repeats_too_much(self):
        return self.state_repeat_counter > config.config.max_state_repeat

    def create_train_data(self, method_num, global_step, agent):
        assert len(self.experience[-1]) >= 2
        called_methods_bits = self.experience[-1][-1].called_methods
        reward_rising_rate = self.__calc_reward_rising(global_step)
        if called_methods_bits == 0:
            for i in range(method_num):
                self.replay_buffer.create_and_append_data(
                    item=self.experience[-1][-1],
                    target_method_id=i, 
                    step_to_call_target=-1, 
                    is_new_path=None,    # Don't care because step_to_call_target == -1.
                    reward_rising_rate=reward_rising_rate,
                    agent=agent
                )
        else:
            for i in range(method_num):
                if (called_methods_bits & (1 << i)) > 0:
                    is_new_path = not self.path_has_been_taken(i)
                    for step_idx, experience_item in enumerate(self.experience[-1][1:], start=1):   # enumerate starts from 1 because self.experience[-1][0].state == None.
                        self.replay_buffer.create_and_append_data(
                            item=experience_item,
                            target_method_id=i, 
                            step_to_call_target=(len(self.experience[-1]) - 1 - step_idx),
                            is_new_path=is_new_path,
                            reward_rising_rate=reward_rising_rate,
                            agent=agent
                        )
    
    def __calc_reward_rising(self, global_step):
        if config.config.off_reward_rising:
            return 1
        else:
            return 1 + global_step * config.config.reward_rise_rate
        
    def path_has_been_taken(self, method_id):
        for episode in self.experience[:-1]:
            for step in episode:
                if (step.called_methods & (1 << method_id)) != 0:
                    if self.current_path == step.path: return True
        for step in self.experience[-1][:-1]:
            if (step.called_methods & (1 << method_id)) != 0:
                if self.current_path == step.path: return True
        return False
    
    def get_current_path(self):
        return self.current_path
    
    def reset_priority(self, agent):
        self.replay_buffer.reset_priority(agent)

    def sample_batch(self):
        return self.replay_buffer.sample()