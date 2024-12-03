import functools
import random
import subprocess
import time

import uiautomator2 as u2                               # type: ignore
from uiautomator2 import DeviceError, RPCUnknownError   # type: ignore

import logger                                   # type: ignore
from gui_tester.component import Component      # type: ignore
from .coverage_manager import CoverageManager   # type: ignore
from .executor import Executor                  # type: ignore
from .observer import Observer                  # type: ignore

class Environment():
    def __init__(self, device_name, config):
        self.device = u2.connect(device_name)
        self.config = config
        self.activities = []
        self.activities_blacklist = []
        self.coverage = CoverageManager(config)
        self.executor = Executor(self.device, config)
        self.observer = Observer(self.config.package, config)

    def check_health(self):
        self.try_uiautomator_process(lambda: self.device.reset_uiautomator())

    def start(self):
        self.try_uiautomator_process(lambda: self.device.press("home"))
        self.__install()

        # Open target app.
        subprocess.run(['adb', 'shell', 'monkey', '-p', self.config.package, '-c', 'android.intent.category.LAUNCHER', '1'])

        if len(self.activities) > 0:
            a = random.choice(self.activities)
            logger.logger.info("Jump to activity %s" % a)
            result = subprocess.run(['adb', 'shell', 'am', 'start', '-n', '{}/.{}'.format(self.config.package, a)], capture_output=True, text=True)
            if result.stderr != "":
                # Can't jump to a.
                self.activities.remove(a)
                self.activities_blacklist.append(a)

    def reset(self):
        self.try_uiautomator_process(lambda: self.device.press("home"))
        self.__uninstall()
        
    def __install(self):
        while True:
            try:
                error = subprocess.run(["adb", "install", self.config.apk_path], timeout=self.config.install_timeout, capture_output=True, text=True).stderr
                if error != "":
                    logger.logger.warning("Install error")
                    logger.logger.warning(error)
                    subprocess.run(["adb", "uninstall", self.config.package])
                    continue
                break
            except subprocess.TimeoutExpired:
                logger.logger.warning("Install timeout expired")
                subprocess.run(["adb", "uninstall", self.config.package])

    def __uninstall(self):
        subprocess.run(["adb", "uninstall", self.config.package])

    def get_components(self):
        for _ in range(self.config.max_try_time_to_empty_screen):   # Handle a situation that there is no item to input but menu buttons.
            xml = self.try_uiautomator_process(lambda: self.device.dump_hierarchy())
            components, status = self.observer.get_components(xml)
            if status == "Empty Screen":
                logger.logger.warning("Empty screen")
                time.sleep(2)
                continue
        return components, status

    def is_out_of_app(self):
        return self.observer.is_out_of_app()
    
    def perform_action(self, action: Component):
        self.executor.perform_action(action)

    def handle_out_of_app(self):
        def process(self):
            self.device.app_start(self.config.package)
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
        # subprocess.run(['adb', 'reboot'])
        # self.device = u2.connect("emulator-5554")
        while True:
            try:
                self.device.reset_uiautomator()
                break
            except Exception as e:
                logger.logger.warning("Reset UIAutomator failed")
                logger.logger.warning(e)
                time.sleep(10)
        logger.logger.warning("Reset UIAutomator succeed.")
        self.__uninstall()

    # def reconnect(self):
    #     subprocess.run(['adb', 'reboot'])
    #     time.sleep(10)
    #     self.device = u2.connect("emulator-5554")
    ##     self.device.reset_uiautomator()

    def try_uiautomator_process(self, process):
        for _ in range(self.config.max_uiautomator_retry):
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