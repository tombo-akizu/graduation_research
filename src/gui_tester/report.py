import csv
import subprocess
import threading

from matplotlib import pyplot as plt

from gui_tester.log_reader import LogReader # type: ignore
from gui_tester.path import Path            # type: ignore
import logger                               # type: ignore
import gui_tester.config as config          # type: ignore

class ReportItem():
    def __init__(self, action, new_state, loss, target_is_called, new_state_status, path):
        self.action = action
        self.new_state = new_state
        self.loss = loss
        self.target_is_called = target_is_called
        self.new_state_status = new_state_status
        self.path = path

class NewPathData():
    def __init__(self, path: Path, global_step):
        self.path = path
        self.global_step = global_step

report_item_log = []
report_path_log = []

def start_logging():
    subprocess.run(["adb", "logcat", "-c"])
    log_thread = threading.Thread(target=log, daemon=True)
    log_thread.start()

def log():
    with open("result/logcat.txt", "w") as f:
        logcat = subprocess.Popen(["adb", "logcat", "*:E"], stdout=f, stderr=subprocess.DEVNULL)
        # try:
        #     for line in iter(logcat.stdout.readline, b''):
        #         decoded_line = line.decode('utf-8').strip()
        #         if config.config.package in decoded_line:
        #             f.write(decoded_line + "\n")
        #             f.flush()
        # finally:
        #     logcat.terminate()
        #     logcat.stdout.close()

def start_new_episode():
    global report_item_log
    report_item_log.append([])

def push(action, new_state, loss, target_is_called, current_path: Path, new_state_status: str, global_step):
    global report_item_log
    global report_path_log
    report_item_log[-1].append(ReportItem(action, new_state, loss, target_is_called, new_state_status, current_path))
    if target_is_called:
        flag = False
        for item in report_path_log:
            if current_path == item.path:
                flag = True
                break
        if not flag:
            report_path_log.append(NewPathData(current_path, global_step))

def output_report():
    global report_item_log
    global report_path_log
    header = ["", "action", "new_state", "new_state_idx", "new_state_status", "loss", "target_is_called", "path"]

    with open("result/path.csv", "w", newline="") as f:
        writer = csv.writer(f)
        for i, report_episode in enumerate(report_item_log):
            writer.writerow(["episode: {}".format(i), "", "", "", "", "", "", ""])
            writer.writerow(header)
            for j, report_item in enumerate(report_episode):
                writer.writerow([
                    str(j), 
                    str(report_item.action), 
                    str(report_item.new_state.get_tuple()), 
                    str(report_item.new_state.id), 
                    report_item.new_state_status,
                    str(report_item.loss), 
                    str(report_item.target_is_called),
                    str(report_item.path)
                    ])
    
    if isinstance(report_item_log[0][0].loss, float):
        losses = []
        for episode in report_item_log:
            for step in episode:
                losses.append(step.loss)
        x = range(len(losses))

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(x, losses, "-", linewidth=1, alpha=1)
        ax.set_xlabel('Step')
        ax.set_ylabel('Loss')
        ax.set_ylim(0, 1)
        fig.savefig("result/loss.png")
    else:
        explorer_losses = []
        caller_losses = []
        for episode in report_item_log:
            for step in episode:
                if step.loss == None:
                    explorer_losses.append(None)
                    caller_losses.append(None)
                else:
                    explorer_losses.append(step.loss[0])
                    caller_losses.append(step.loss[1])
        x = range(len(explorer_losses))

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(x, explorer_losses, "-", linewidth=1, alpha=1)
        ax.set_xlabel('Step')
        ax.set_ylabel('Loss')
        ax.set_ylim(0, 1)
        fig.savefig("result/explorer_loss.png")

        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.plot(x, caller_losses, "-", linewidth=1, alpha=1)
        ax.set_xlabel('Step')
        ax.set_ylabel('Loss')
        ax.set_ylim(0, 1)
        fig.savefig("result/caller_loss.png")

    steps = []
    for item in report_path_log:
        steps.append(item.global_step)

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.hist(steps, bins=16)
    ax.set_xlabel('Step')
    ax.set_ylabel('Found new path')
    fig.savefig("result/found_new_path.png")

    for item in report_path_log:
        logger.logger.info("Path {} is found at {}'th step.".format(item.path, item.global_step))

    with open("result/path.txt", "w") as f:
        f.write(str(len(report_path_log)))

    LogReader().read_log()