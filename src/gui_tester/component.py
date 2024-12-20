import re

import gui_tester.config as config  # type: ignore

# List of GUI group's key.
# Components with the same resource-id and actionabilities are in the same component group.
component_group_list = []

class Component():
    def __init__(
            self,
            label: str,
            bounds: tuple((int, int, int, int)),    # type: ignore
            component_class: str,
            resource_id: str,
            is_clickable: bool,
            is_long_clickable: bool,
            is_scrollable: bool,
            is_checkable: bool
                 ):
        self.label = label
        assert(len(bounds) == 4)
        self.bounds = bounds
        self.component_class = component_class
        self.resource_id = resource_id
        self.is_clickable = is_clickable
        self.is_long_clickable = is_long_clickable
        self.is_scrollable = is_scrollable
        self.is_checkable = is_checkable

        global component_group_list
        key = self.get_group_key()
        if key in component_group_list:
            self.id = component_group_list.index(key)
        else:
            self.id = len(component_group_list)
            component_group_list.append(key)

        assert len(component_group_list) <= config.config.state_size
        
    def from_node(node, label):
        bounds = Component.__get_bound_from_string(node.attrib["bounds"])
        return Component(label,
                bounds,
                node.attrib["class"],
                node.attrib["resource-id"],
                node.attrib["clickable"] == "true",
                node.attrib["long-clickable"] == "true",
                node.attrib["scrollable"] == "true",
                node.attrib["checkable"] == "true")
    
    # Returns key of GUI group.
    def get_group_key(self):
        return (
            self.resource_id,
            self.is_clickable,
            self.is_long_clickable,
            self.is_scrollable,
            self.is_checkable
            )
    
    def __get_bound_from_string(bound_string):
        coordinate = re.findall(r'\d+', bound_string)
        left = int(coordinate[0])
        top = int(coordinate[1])
        right = int(coordinate[2])
        bottom = int(coordinate[3])
        return (left, top, right, bottom)
    
    def get_bound_center(self):
        return (
            (self.bounds[0] + self.bounds[2]) / 2., 
            (self.bounds[1] + self.bounds[3]) / 2.
            )