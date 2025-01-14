import re

class StackTrace:
    def __init__(self):
        self.lines: list(str) = []
        self.count = 1
        self.package = ""

    def append(self, line: str):
        self.lines.append(line)

    def count_up(self):
        self.count += 1

    def set_package(self, package: str):
        self.package = package

    def __eq__(self, other):
        if other == None: return False
        return self.lines == other.lines    # Python compares lists deeply.

    def __str__(self):
        out = "count: {}\npackage: {}\n".format(self.count, self.package)
        for line in self.lines:
            out += line + "\n"
        return out

class LogReader:
    def __init__(self):
        self.stacktrace_history: list(StackTrace) = []
        self.current_stacktrace = None

    def read_log(self):
        source = open("result/logcat.txt", "r")

        current_process_id = -1
        current_thread_id = -1

        for line in source:
            if self.current_stacktrace != None:
                package_result = re.search(r'Process:\s+([\w\.]+),\s+PID:', line)
                if package_result:
                    self.current_stacktrace.set_package(package_result.group(1))
                    continue

                result = re.search(r'[\d\-]+\s+[\d\:\.]+\s+(\d+)\s+(\d+)\s+E\s+(.*)\n', line)
                if result and result.group(1) == current_process_id and result.group(2) == current_thread_id:
                    self.current_stacktrace.append(result.group(3))
                else:
                    if self.current_stacktrace in self.stacktrace_history:
                        index = self.stacktrace_history.index(self.current_stacktrace)
                        self.stacktrace_history[index].count_up()
                    else:
                        self.stacktrace_history.append(self.current_stacktrace)
                    self.current_stacktrace = None

            result = re.search(r'[\d\-]+\s+[\d\:\.]+\s+(\d+)\s+(\d+).*FATAL EXCEPTION', line)
            if result:
                current_process_id = result.group(1)
                current_thread_id = result.group(2)
                self.current_stacktrace = StackTrace()

        source.close()

        with open("result/crash_log.txt", "w") as out:
            for stacktrace in self.stacktrace_history:
                out.write(str(stacktrace) + "\n")

if __name__ == "__main__":
    log_reader = LogReader()
    log_reader.read_log()