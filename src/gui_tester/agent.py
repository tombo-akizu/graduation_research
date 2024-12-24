import random

import gui_tester.config as config  # type: ignore

class Agent():
    def __init__(self):
        self.epsilon = config.config.epsilon_start
        self.epsilon_step = (config.config.epsilon_start - config.config.epsilon_end) / (config.config.epsilon_episode_end - config.config.epsilon_episode_start)

        # Loss value cache.
        self.loss = 0

    # Update epsilon of the epsilon-greedy method.
    def update_epsilon(self, current_episode):
        if (current_episode >= config.config.epsilon_episode_start) and (current_episode < config.config.epsilon_episode_end):
            self.epsilon = config.config.epsilon_start - self.epsilon_step * (current_episode - config.config.epsilon_episode_start)
    
    def select_action_randomly(self, components):
        return random.choice(components)

    def get_loss(self):
        # loss will be updated by SingleNetAgent.optimize_model or MultiNetAgent.optimize_model.
        return self.loss
    
# Factory function to create appropriate child-class instance.
def create():
    if config.config.model == "4LP" or config.config.model == "4LPWithPath" or config.config.model == "LSTM":
        # Import late to avoid circular import error...
        import gui_tester.singlenet_agent as singlenet_agent    # type: ignore
        return singlenet_agent.SingleNetAgent()
    elif config.config.model == "Multi":
        import gui_tester.multinet_agent as multinet_agent      # type: ignore
        return multinet_agent.MultiNetAgent()
    else:
        assert False, "Invalid model name."