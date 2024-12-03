import os
import subprocess
import xml.etree.ElementTree as ET

class CoverageManager():
    def __init__(self, config):
        self.config = config
        self.index = 0
        self.line_coverage = 0

    def update_coverage(self):
        subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', './script/dumpCoverageOnce.ps1', self.config.package, "./result", str(self.index)])

        tree = ET.parse('{}/coverage{}/coverage.xml'.format("./result", self.index))
        root = tree.getroot()

        # Count missed and covered items.
        coverage_data = {
            "INSTRUCTION": {"missed": 0, "covered": 0},
            "LINE": {"missed": 0, "covered": 0},
            "BRANCH": {"missed": 0, "covered": 0}
        }

        # For each class
        for counter in root.iter('counter'):
            counter_type = counter.attrib['type']
            missed = int(counter.attrib['missed'])
            covered = int(counter.attrib['covered'])
            
            # type: instruction, line, branch
            if counter_type in coverage_data:
                coverage_data[counter_type]["missed"] += missed
                coverage_data[counter_type]["covered"] += covered

        def calculate_coverage(missed, covered):
            total = missed + covered
            if total == 0:
                return 0
            return (float(covered) / total) * 100
        
        coverages = []

        for _coverage_type, data in coverage_data.items():
            coverage = calculate_coverage(data['missed'], data['covered'])
            coverages.append(coverage)

        self.line_coverage = coverages[1]
        self.index += 1

    def get_coverage(self):
        return self.line_coverage

    def merge_coverage(self):
        command = ["java", "-jar", "script/jacococli.jar", "merge"]
        for i in range(self.index):
            ecpath = "result/coverage{}/coverage.ec".format(i)
            if os.path.isfile(ecpath):
                command.append(ecpath)
        command.append("--destfile")
        command.append("result/output.ec")
        subprocess.run(command)