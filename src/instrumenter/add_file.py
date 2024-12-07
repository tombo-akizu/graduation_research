import os
import re

def add_file(method_num):
    with open("template/CallReport.java", "r") as f:
        code = f.read()

    modified_code = modify_str(code, method_num)

    os.mkdir("project/app/src/main/java/callreport")
    with open("project/app/src/main/java/callreport/CallReport.java", "w") as f:
        f.write(modified_code)

def modify_str(target, method_num):
    return re.sub(r"METHOD_NUM = \d+;", "METHOD_NUM = {};".format(method_num) ,target)