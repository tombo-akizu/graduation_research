import torch

class Path:
    OUT_OF_APP = -1

    def __init__(self):
        self.path_list = []

    def append(self, state_id: int):
        self.path_list.append(state_id)
        self.cut_loop()
        return self

    def clone(self):
        return Path.create_clone(self.path_list)

    def get_tensor(self, config):
        bool_list = [False] * (config.state_size + 1)
        for state in self.path_list:
            if state == Path.OUT_OF_APP:
                bool_list[-1] = True
            else:
                bool_list[state] = True
        return torch.tensor(bool_list, dtype=torch.bool)
    
    def get_path_sequence_tensor(self, experience, config):
        tensors = []
        for state_id in self.path_list:
            if state_id == Path.OUT_OF_APP:
                tensors.append(torch.tensor([0] * config.state_size, dtype=torch.float32))
            else:
                tensors.append(torch.tensor(experience.state_list[state_id], dtype=torch.float32))
        return torch.stack(tensors)
    
    def append_out_of_app(self):
        self.path_list.append(Path.OUT_OF_APP)
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
    
    def __eq__(self, other):
        if not isinstance(other, Path):
            return NotImplemented
        return self.path_list == other.path_list    # Python compares list deeply.
    
    def __str__(self):
        return str(self.path_list)

    def create_clone(path_list):
        new_path = Path()
        new_path.path_list = path_list.copy()
        return new_path