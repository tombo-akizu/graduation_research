import random
import re

from uiautomator2 import UiObjectNotFoundError  # type: ignore

from gui_tester.component import Component  # type: ignore
import logger                               # type: ignore
import gui_tester.config as config          # type: ignore

class Executor():
    def __init__(self, device):
        self.device = device

    def perform_action(self, action: Component):
        try:
            bound_center = action.get_bound_center()
            if action.label == "Input":
                if re.search(r'(?i)(EditText|SearchBox|AutoCompleteTextView|AutoSuggestView|Field|Input)', action.resource_id):
                    self.device.click(*bound_center)    # * is unpack operator.
                    self.__set_text(action)
                    self.press_ok()
                    logger.logger.info("Action performed: Input Text")
                elif "Bar" in action.resource_id:
                    self.device.swipe(bound_center[0], bound_center[1], config.config.emulator_screen_width / 2, bound_center[1])
                    logger.logger.info("Action performed: Swipe to center")
                else:
                    self.device.click(*bound_center)
            elif action.resource_id == "com.android.systemui:id/menu":
                self.device.press("menu")
                logger.logger.info("Action performed: Press menu")
            elif action.resource_id == "com.android.systemui:id/back":
                self.device.press("back")
                logger.logger.info("Action performed: Press back")
            elif self.device(resourceId=action.resource_id, scrollable=True).exists:
                self.__perform_scroll(action)
                logger.logger.info("Action performed: Scroll")
            else:
                r = random.random()
                if 0. <= r < 0.7:
                    self.device.click(*bound_center)
                    logger.logger.info("Action performed: Click")
                elif 0.7 <= r < 0.8:
                    self.device.long_click(*bound_center)
                    logger.logger.info("Action performed: Long click")
                elif 0.8 <= r < 0.9:  # Swipe from center to left border of the screen
                    self.device.swipe(bound_center[0], bound_center[1], 0, bound_center[1], 1)
                    logger.logger.info("Action performed: Swipe left")
                elif 0.9 <= r <= 1.:  # Swipe from center to the right border of the screen
                    self.device.swipe(bound_center[0], bound_center[1], config.config.emulator_screen_width, bound_center[1], 1)
                    logger.logger.info("Action performed: Swipe right")
        except UiObjectNotFoundError as e:
            logger.logger.warning(e)
    
    def __set_text(self, action):
        assert self.device(resourceId=action.resource_id).exists
        le = random.randint(1, 16)
        r = random.random()
        if 0. <= r < 0.5:
            arr = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        elif 0.5 <= r < 0.75:
            arr = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        else:
            arr = list('(*&^%$#@!{abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
        text = ''.join(random.choice(arr) for _ in range(le))
        self.device(resourceId=action.resource_id).set_text(text)
        self.device.press("back")

    def press_ok(self):
        if self.device.exists(text="OK"):
            self.device(text="OK").click()
            return
        if self.device.exists(text="Save"):
            self.device(text="Save").click()
            return
        if self.device.exists(text="Next"):
            self.device(text="Next").click()
            return
        if self.device.exists(text="Confirm"):
            self.device(text="Confirm").click()
            return

    def __perform_scroll(self, action):
        # Steps must be larger than 1 to correctly scroll.
        self.device(resourceId=action.resource_id, scrollable=True).scroll.toEnd(steps=2)