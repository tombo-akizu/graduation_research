import gui_tester.config as config  # type: ignore
from gui_tester.path import Path                                # type: ignore
from gui_tester.replay_buffer import ReplayBuffer, TrainData    # type: ignore
from gui_tester.state import State                              # type: ignore

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
class Experience():
    def __init__(self):
        # 2-dimentional list. Each item is list[ExperienceItem] of an episode.
        self.experience = []
        self.state_repeat_counter = 0
        self.replay_buffer = ReplayBuffer()

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
        if called_methods_bits == 0:
            for i in range(method_num):
                experience_item = self.experience[-1][-1]
                data = TrainData(
                    i,
                    experience_item.state, 
                    experience_item.action_idx, 
                    -0.001,
                    experience_item.new_state, 
                    experience_item.path.clone()
                )
                if not config.config.off_per:
                    data.set_priority(agent, self)
                self.replay_buffer.push(data)
        else:
            for i in range(method_num):
                if (called_methods_bits & (1 << i)) > 0:
                    for step_idx, experience_item in enumerate(self.experience[-1][1:], start=1):   # enumerate starts from 1 because self.experience[-1][0].state == None.
                        step_num = self.__step_num_to_call_method(step_idx, i)
                        data = TrainData(
                            i, 
                            experience_item.state, 
                            experience_item.action_idx, 
                            self.__calc_reward(step_num, i, global_step), 
                            experience_item.new_state, 
                            experience_item.path.clone()
                            )
                        if not config.config.off_per:
                            data.set_priority(agent, self)
                        self.replay_buffer.push(data)
    
    def __step_num_to_call_method(self, departure, method_id):
        step_idx = departure
        step_num = 0
        method_bit = 1 << method_id
        while (self.experience[-1][step_idx].called_methods & method_bit) == 0:
            step_idx += 1
            step_num += 1
        return step_num
    
    def __calc_reward(self, step_num, method_id, global_step):
        if step_num == 0:
            if self.path_has_been_taken(method_id):
                return -0.001
            return 1 * self.__calc_reward_rising(global_step)
        if self.path_has_been_taken(method_id):
            return -0.001
        return 0.01 * (config.config.discount_rate ** step_num) * self.__calc_reward_rising(global_step)
        
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
        self.replay_buffer.reset_priority(agent, self)

    def sample_batch(self):
        return self.replay_buffer.sample()