import csv

from matplotlib import pyplot as plt

from gui_tester.path import Path
import logger

class ReportItem():
    def __init__(self, action, new_state, new_state_id, loss, target_is_called, new_state_status, path):
        self.action = action
        self.new_state = new_state
        self.new_state_id = new_state_id
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

def start_new_episode():
    global report_item_log
    report_item_log.append([])

def push(action, new_state, new_state_id, loss, target_is_called, current_path: Path, new_state_status: str, global_step):
    global report_item_log
    global report_path_log
    report_item_log[-1].append(ReportItem(action, new_state, new_state_id, loss, target_is_called, new_state_status, current_path))
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
                    str(report_item.new_state), 
                    str(report_item.new_state_id), 
                    report_item.new_state_status,
                    str(report_item.loss), 
                    str(report_item.target_is_called),
                    str(report_item.path)
                    ])
                
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

    steps = []
    for item in report_path_log:
        steps.append(item.global_step)

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.hist(steps, bins=16)
    ax.set_xlabel('Step')
    ax.set_ylabel('Found new path')
    fig.savefig("result/found_new_pass.png")

    for item in report_path_log:
        logger.logger.info("Path {} is found at {}'th step.".format(item.path, item.global_step))

    with open("result/path.txt", "w") as f:
        f.write(str(len(report_path_log)))