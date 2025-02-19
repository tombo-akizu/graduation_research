import random

import gui_tester.config as config  # type: ignore

class Agent():
    def __init__(self):
        self.epsilon = config.config.epsilon_start
        self.epsilon_step = (config.config.epsilon_start - config.config.epsilon_end) / (config.config.epsilon_episode_end - config.config.epsilon_episode_start)

    # Update epsilon of the epsilon-greedy method.
    def update_epsilon(self, current_episode):
        if (current_episode >= config.config.epsilon_episode_start) and (current_episode < config.config.epsilon_episode_end):
            self.epsilon = config.config.epsilon_start - self.epsilon_step * (current_episode - config.config.epsilon_episode_start)
    
    def select_action_randomly(self, components):
        return random.choice(components)
