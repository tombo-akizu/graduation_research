import torch

import gui_tester.config as config  # type: ignore
from gui_tester.state import State  # type: ignore

class Path:
    def __init__(self):
        self.path_list = []

    def append(self, state: State):
        self.path_list.append(state)
        self.cut_loop()
        return self

    def clone(self):
        return Path.create_clone(self.path_list)

    # Get set of covered states.
    def get_tensor(self):
        # The last item is for OUT_OF_APP state.
        bool_list = [False] * (config.config.state_size + 1)
        for state in self.path_list:
            if state.is_out_of_app:
                bool_list[-1] = True
            else:
                bool_list[state.id] = True
        return torch.tensor(bool_list, dtype=torch.bool)
    
    # Get sequence of covered states.
    def get_path_sequence_tensor(self):
        tensors = []
        for state in self.path_list:
            tensors.append(state.get_tensor())
        return torch.stack(tensors)
    
    def append_out_of_app(self):
        self.path_list.append(State.create_out_of_app())
        self.cut_loop()

    def cut_loop(self):
        if len(self.path_list) < 2:
            return
        if self.path_list[-2] == self.path_list[-1]:
            self.path_list = self.path_list[:-1]
            return
        indices = [i for i, item in enumerate(self.path_list) if item == self.path_list[-1]]
        if len(indices) < 3:
            return
        for i, idx in enumerate(indices[:-2]):
            if self.path_list[idx:indices[i + 1]] == self.path_list[indices[-2]:indices[-1]]:
                self.path_list = self.path_list[:(indices[-2] + 1)]

    def get_path_sequence_tuple(self):
        return tuple([state.id for state in self.path_list])
    
    def __eq__(self, other):
        if not isinstance(other, Path):
            return NotImplemented
        return self.path_list == other.path_list    # Python compares list deeply.
    
    def __str__(self):
        out = ""
        for state in self.path_list:
            out += str(state) + ", "
        return out

    def create_clone(path_list):
        new_path = Path()
        new_path.path_list = path_list.copy()
        return new_path