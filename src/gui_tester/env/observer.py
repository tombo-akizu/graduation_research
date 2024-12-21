import random
import re
import subprocess
import xml.etree.ElementTree as ET

from logger import logger                   # type: ignore
from gui_tester.component import Component  # type: ignore
import gui_tester.config as config          # type: ignore

class Observer():
    def __init__(self):
        self.allow_packages = [config.config.package, "com.android.packageinstaller", "PopupWindow", "com.google.android.permissioncontroller", "com.android.internal.app.ResolverActivity"]
        self.group_regex = {
            "Input": r'(?i)(EditText|SearchBox|AutoCompleteTextView|AutoSuggestView|Field|Input|CheckBox|DatePicker|RadioButton|CheckedTextView|Switch|SeekBar)',
            "Button": r'(?i)(Button|GlyphView|ListItem)',
            "Navigation": r'(?i)(Toolbar|TitleBar|ActionBar|Menu|Navigation|SideBar|Drawer|AppBar|TabWidget)',
            "List": r'(?i)(ListView|RecyclerView|ListPopUpWindow|GridView|GroupView)'
        }

    def get_components(self, xml):
        root = ET.fromstring(xml)
        status = "Fine"
        if len(root) == 0:  # Handle a situation that there is no item to input but menu buttons. TODO: Is this correctly works?
            status = "Empty Screen"
        elif self.__is_stopped_screen(root):
            logger.warning("is stopped screen")
            status = "Stopped Screen"
        elif self.is_out_of_app():
            status = "Out of App"

        self.__passing_actionable_to_children(root)
        components = []
        self.__collect_component(root, components)
            
        components.append(Component(
                "Navigation",
                (150.0,150.0,150.0,150.0),
                "com.android.systemui:id/back",
                "com.android.systemui:id/back",
                False, False, False, False))  
        components.append(Component(
                "Navigation",
                (150.0,150.0,150.0,150.0),
                "com.android.systemui:id/menu",
                "com.android.systemui:id/menu",
                False, False, False, False))
        random_x = config.config.emulator_screen_width * random.uniform(0.1, 0.9)
        random_y = config.config.emulator_screen_height * random.uniform(0.1, 0.9)          
        components.append(Component("Button",
                (random_x, random_y, random_x, random_y),
                "Random.Touch",
                "Random.Touch",
                True, False, False, False))
        return tuple(set(components)), status
    
    def __is_stopped_screen(self, node):
        if "text" in node.attrib and "has stopped" in node.attrib["text"]:
            return True
        for child in node:
            if self.__is_stopped_screen(child):
                return True
        return False

    # Passing actionable to children node.
    # If the parent node is clickable, the children also get clickable.
    def __passing_actionable_to_children(self, node):
        actionable = ["clickable", "long-clickable", "scrollable", "checkable"]
        if len(list(node)) == 0:
            return
        for child in node:
            for action in actionable:
                if action in node.attrib and node.attrib[action] == 'true':
                    child.set(action, "true")
            self.__passing_actionable_to_children(child)

    # Append actionable component in components argument.
    def __collect_component(self, node, components):
        if "package" in node.attrib and node.attrib["package"] in self.allow_packages:
            if re.search(self.group_regex["Navigation"], node.attrib["class"]):
                label = "Navigation"
            elif re.search(self.group_regex["List"], node.attrib["class"]):
                label = "List"
            elif re.search(self.group_regex["Input"], node.attrib["class"]) and self.__is_actionable(node):
                label = "Input"
            elif self.__is_actionable(node):
                label = "Button"
            else:
                label = None
            if label and not "com.android.systemui:id/home" in node.attrib["resource-id"] and not "com.android.systemui:id/recent_apps" in node.attrib["resource-id"]:
                components.append(Component.from_node(node, label))

        for child in node:
            self.__collect_component(child, components)

    def __is_actionable(self, node):
            return node.attrib["clickable"] == "true" or node.attrib["long-clickable"] == "true" or node.attrib[
                "scrollable"] == "true" or node.attrib["checkable"] == "true" or node.attrib["focusable"] == "true"
    
    # Current screen is in allowed ones or not.
    def is_out_of_app(self):
        output = subprocess.run(["adb", "shell", "dumpsys", "window"], capture_output=True, text=True).stdout
        output = Observer.__grep(output, "mCurrentFocus")
        for p in self.allow_packages:
            if p in output:
                logger.debug("Is not out_of_app {}".format(output))
                return False
        logger.debug("Is out_of_app {}".format(output))
        return True

    def __grep(multiline_string, search_string):
        output = ""

        lines = multiline_string.splitlines()
        
        for line in lines:
            if search_string in line:
                output += line
        
        return output
    
    def get_current_activity(self):
        output = subprocess.run(['adb', 'shell', 'dumpsys', 'window'], capture_output=True, text=True).stdout
        output = Observer.__grep(output, "mCurrentFocus")
        if "Application Error" in output:
            return "Application Error", False
        is_of_target_application = config.config.package in output
        activity_name = output.split('/')[-1].replace(config.config.package + '.', '').split('}')[0]    # original
        return activity_name, is_of_target_application