from gui_tester.path import Path                                # type: ignore
from gui_tester.replay_buffer import ReplayBuffer, TrainData    # type: ignore

class ExperienceItem():
    def __init__(self, state_id: int, action_idx: int, new_state_id: int, called_methods: int, path: Path):
        self.state_id = state_id
        self.action_idx = action_idx
        self.new_state_id = new_state_id
        self.called_methods = called_methods
        self.path = path

# Experience manages the following data.
# - Experience in reinforcement learning context:   experience
# - Traning data created from experience:           replay_buffer
# - How many times the same state repeats:          state_repeat_counter
class Experience():
    def __init__(self, config):
        # 2-dimentional list. Each item is list[ExperienceItem] of an episode.
        self.experience = []
        self.state_repeat_counter = 0
        self.config = config
        self.replay_buffer = ReplayBuffer(config)

        # List of unique states. state_id is the index in state_list.
        self.state_list = []

        self.current_path = Path()

    def start_new_episode(self):
        self.experience.append([])
        self.state_repeat_counter = 0
        self.current_path = Path()

    def append(self, state: tuple, action_idx: int, new_state: tuple, called_methods: int):
        state_id = self.get_state_id(state)
        new_state_id = self.get_state_id(new_state)
        self.current_path.append(new_state_id)
        self.experience[-1].append(ExperienceItem(state_id, action_idx, new_state_id, called_methods, self.current_path.clone()))
        if state_id == new_state_id:
            self.state_repeat_counter += 1
        else:
            self.state_repeat_counter = 0

    def append_out_of_app(self):
        self.current_path.append_out_of_app()

    def state_repeats_too_much(self):
        return self.state_repeat_counter > self.config.max_state_repeat

    def create_train_data(self, method_num, global_step, agent):
        assert len(self.experience[-1]) >= 2
        called_methods_bits = self.experience[-1][-1].called_methods
        if called_methods_bits == 0:
            for i in range(method_num):
                experience_item = self.experience[-1][-1]
                data = TrainData(
                    i,
                    self.state_list[experience_item.state_id], 
                    experience_item.action_idx, 
                    -0.001,
                    self.state_list[experience_item.new_state_id], 
                    experience_item.path.clone()
                )
                if not self.config.off_per:
                    data.set_priority(agent, self)
                self.replay_buffer.push(data)
        else:
            for i in range(method_num):
                if (called_methods_bits & (1 << i)) > 0:
                    for step_idx, experience_item in enumerate(self.experience[-1][1:], start=1):   # enumerate starts from 1 because self.experience[-1][0].state == None.
                        step_num = self.__step_num_to_call_method(step_idx, i)
                        data = TrainData(
                            i, 
                            self.state_list[experience_item.state_id], 
                            experience_item.action_idx, 
                            self.__calc_reward(step_num, i, global_step), 
                            self.state_list[experience_item.new_state_id], 
                            experience_item.path.clone()
                            )
                        if not self.config.off_per:
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
        return 0.01 * (self.config.discount_rate ** step_num) * self.__calc_reward_rising(global_step)
        
    def __calc_reward_rising(self, global_step):
        if self.config.off_reward_rising:
            return 1
        else:
            return 1 + global_step * self.config.reward_rise_rate
        
    def path_has_been_taken(self, method_id):
        for episode in self.experience[:-1]:
            for step in episode:
                if (step.called_methods & (1 << method_id)) != 0:
                    if self.current_path == step.path: return True
        for step in self.experience[-1][:-1]:
            if (step.called_methods & (1 << method_id)) != 0:
                if self.current_path == step.path: return True
        return False

    def get_state_id(self, state):
        if not state in self.state_list:
            self.state_list.append(state)
            return len(self.state_list) - 1
        return self.state_list.index(state)
    
    def get_current_path(self):
        return self.current_path
    
    def reset_priority(self, agent):
        self.replay_buffer.reset_priority(agent, self)