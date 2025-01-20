import functools
import random
import subprocess
import time

import uiautomator2 as u2                               # type: ignore
from uiautomator2 import DeviceError, RPCUnknownError   # type: ignore

import logger                                   # type: ignore
import gui_tester.config as config              # type: ignore
from gui_tester.component import Component      # type: ignore
from .coverage_manager import CoverageManager   # type: ignore
from .executor import Executor                  # type: ignore
from .observer import Observer                  # type: ignore

class Environment():
    def __init__(self, device_name):
        self.device = u2.connect(device_name)
        self.activities = []
        self.activities_blacklist = []
        self.selected_activity = ""
        self.coverage = CoverageManager()
        self.executor = Executor(self.device)
        self.observer = Observer()

    def check_health(self):
        self.try_uiautomator_process(lambda: self.device.reset_uiautomator())

    def start(self):
        self.try_uiautomator_process(lambda: self.device.press("home"))

        if len(self.activities) > 0:
            # Open the target app with an activity.
            self.selected_activity = random.choice(self.activities)
            logger.logger.info("Jump to activity %s" % self.selected_activity)
            self.device.app_start(config.config.package, self.selected_activity)
        else:
            # Open the target app with the initial activity.
            self.device.app_start(config.config.package)

    def exclude_selected_activity(self):
        self.activities.remove(self.selected_activity)
        self.activities_blacklist.append(self.selected_activity)
        logger.logger.info("Blacklist appending happens on exclude_current_activity.")

    def reset(self):
        self.try_uiautomator_process(lambda: self.device.press("home"))
        # self.__uninstall()
        # self.device.app_clear(config.config.package)
        subprocess.run(["adb", "shell", "am", "force-stop", config.config.package])
        subprocess.run(["adb", "shell", "am", "kill-all"])
        
    def install(self):
        while True:
            try:
                error = subprocess.run(["adb", "install", config.config.apk_path], timeout=config.config.install_timeout, capture_output=True, text=True).stderr
                if error != "":
                    logger.logger.warning("Install error")
                    logger.logger.warning(error)
                    subprocess.run(["adb", "uninstall", config.config.package])
                    continue
                break
            except subprocess.TimeoutExpired:
                logger.logger.warning("Install timeout expired")
                subprocess.run(["adb", "uninstall", config.config.package])

    def uninstall(self):
        subprocess.run(["adb", "uninstall", config.config.package])

    def get_components(self):
        for _ in range(config.config.max_try_time_to_empty_screen):   # Handle a situation that there is no item to input but menu buttons.
            xml = self.try_uiautomator_process(lambda: self.device.dump_hierarchy())
            components, status = self.observer.get_components(xml)
            if status == "Empty Screen":
                logger.logger.warning("Empty screen")
                time.sleep(2)
                continue
            elif status == "Stopped Screen":
                logger.logger.warning("Stopped screen")
        return components, status

    def is_out_of_app(self):
        return self.observer.is_out_of_app()
    
    def perform_action(self, action: Component):
        self.executor.perform_action(action)

    def handle_out_of_app(self):
        def process(self):
            self.device.app_start(config.config.package)
            time.sleep(2)
        self.try_uiautomator_process(functools.partial(process, self=self))

    def get_current_activity(self):
        return self.observer.get_current_activity()
    
    def append_activity(self, activity_name):
        if not activity_name in self.activities and not activity_name in self.activities_blacklist:
            self.activities.append(activity_name)

    def update_coverage(self):
        self.coverage.update_coverage()

    def get_coverage(self):
        return self.coverage.get_coverage()

    def merge_coverage(self):
        self.coverage.merge_coverage()

    def reboot(self):
        while True:
            try:
                self.device.reset_uiautomator()
                break
            except Exception as e:
                logger.logger.warning("Reset UIAutomator failed")
                logger.logger.warning(e)
                time.sleep(10)
        logger.logger.warning("Reset UIAutomator succeed.")
        # self.device.app_clear(config.config.package)
        subprocess.run(["adb", "shell", "am", "force-stop", config.config.package])
        subprocess.run(["adb", "shell", "am", "kill-all"])


    def try_uiautomator_process(self, process):
        for _ in range(config.config.max_uiautomator_retry):
            try:
                return process()
            except (DeviceError, RPCUnknownError) as e:
                self.reboot()
                logger.logger.warning(e)
                continue
            except Exception as e:
                self.reboot()
                logger.logger.warning("An exception not caught by UIAutomator occured...")
                logger.logger.warning(e)
                continue
        raise e