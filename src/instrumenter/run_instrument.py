import os
import shutil
import sys
import instrumenter.add_file as add_file            # type: ignore
from instrumenter.instrument import Instrumenter    # type: ignore

def run_instrument(project_root):
    if not os.path.exists(os.path.join(project_root, "app/src/main")):
        print("Give root directory of the project.")
        sys.exit(1)

    if os.path.exists(os.path.join(project_root, "app/src/main/java/callreport")):
        print("This project seems to be already instrumented...")
        sys.exit(2)

    if os.path.isdir("project"):
        shutil.rmtree("project")
 
    shutil.copytree(project_root, "project", ignore=shutil.ignore_patterns(".git", ".gitignore"))
    # Collect source files
    java_path_list = []
    kt_path_list = []
    for cur_dir, dirs, files in os.walk("project/app/src/main"):
        cur_dir = cur_dir.replace(os.sep,'/')
        for file_name in files:
            if file_name == "EndCoverageBroadcast.java":
                # This is an instrumented file by COSMO, not a file of the original application.
                continue
            base_name, extension = os.path.splitext(file_name)
            if extension == ".java":
                java_path_list.append(cur_dir + '/' + file_name)
            elif extension == ".kt":
                kt_path_list.append(cur_dir + '/' + file_name)

    # Insert call of CallReport.callreport.
    instrumenter = Instrumenter()
    for java_path in java_path_list:
        instrumenter.instrument(java_path)

    # Add template/CallReport.java into the project.
    add_file.add_file(instrumenter.get_method_num())

    instrumenter.save_instrumentdata("instrument_data/instrument.pkl")