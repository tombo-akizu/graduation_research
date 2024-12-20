import torch

from gui_tester.component import Component  # type: ignore
import gui_tester.config as config          # type: ignore

state_list = []

class State:
    def __init__(self, components: list[Component], is_out_of_app=False):
        if not is_out_of_app:
            component_group_id_vector = [0] * config.config.state_size
            for component in components:
                component_group_id_vector[component.id] += 1

            # Each item of state-embedding vector is count of GUI components in a component group.
            state = tuple(component_group_id_vector)

            global state_list
            if state in state_list:
                self.id = state_list.index(state)
            else:
                self.id = len(state_list)
                state_list.append(state)
        else:
            self.id = -1

        self.is_out_of_app = is_out_of_app

    def get_tuple(self):
        global state_list
        return state_list[self.id]

    def get_tensor(self):
        if self.is_out_of_app:
            return torch.tensor([0] * config.config.state_size, dtype=torch.float32)
        else:
            global state_list
            return torch.tensor(state_list[self.id], dtype=torch.float32)
        
    def __eq__(self, other):
        if other == None: return False
        if self.id != other.id: return False
        return True
    
    def __str__(self):
        return str(self.id)
        
    def create_out_of_app():
        return State(None, True)