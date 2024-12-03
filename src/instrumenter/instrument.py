import re
import sys
import pickle

from instrument_data import InstrumentData  # type: ignore

class Instrumenter:
    def __init__(self):
        self.method_id = 0
        self.instrument_data: list[InstrumentData] = []

    # Instrument a file.
    def instrument(self, path):
        with open(path, 'r') as file:
            java_code = file.read()

            modified_code = self.__add_report_call(java_code, path)
            modified_code = self.__add_import(modified_code)

        with open(path, 'w') as file:
            file.write(modified_code)

    def __add_report_call(self, java_code, file_path):

        # Insert CallReport.report call in a matched method.
        def insert_report_call(match):
            access = non_none_str(match["access"])
            static = non_none_str(match["static"])
            return_type = match["type"]
            name = non_none_str(match["name"])
            args = non_none_str(match["args"])
            throws = non_none_str(match["throws"])
            body = non_none_str(match["body"])

            method_declaration = access + " " + static + " " + return_type + " " + name + " (" + args + ") " + throws 

            # Insert just after super() or this().
            modified_body = re.sub(
                r'(\b(?:super|this)\s*\((:?.*)\);\s*)',
                rf'\1\nCallReport.report({self.method_id});\n',
                body,
                count=1
            )

            # If there is no super or this call, insert just after declaration of method.
            if modified_body == body:
                modified_body = f'\nCallReport.report({self.method_id});\n' + body
            
            # Save correspondence of method and method_id.
            self.instrument_data.append(InstrumentData(self.method_id, file_path, method_declaration))

            self.method_id += 1

            return method_declaration + "{" + modified_body + "}"

        # Find declarations of methods and apply insert_report_call each of them.
        modified_code = re.sub(
            r'\b(?P<access>(private|public|protected))?\s*(?P<static>static)?\s*(?P<type>(?!private|public|protected|if|for|while|switch|catch)[\w<>]+)(\s+(?P<name>(?!if|for|while|switch|catch)\w+))?\s*\((?P<args>([\w\s,<>\[\]@]|\.\.\.)*?)\)\s*(?P<throws>throws\s*[\w,\s]+)?\s*\{(?P<body>.*?)\}',
            insert_report_call,
            java_code,
            flags=re.DOTALL
        )

        return modified_code

    # Add import callreport.CallReport; in a java_code.
    def __add_import(self, java_code):
        modified_code = None
        if "import" in java_code:
            #  If import statement is in java_code, add "import callreport.CallReport;" following the first import statement.
            modified_code = re.sub(r'(import\s+[a-zA-Z0-9.]+;\s*)', r'\1import callreport.CallReport;\n', java_code, count=1)
        else:
            # If there is no import statement in java_code, add "import callreport.CallReport;" following the package statement.
            modified_code = re.sub(r'(\bpackage\s+[a-zA-Z0-9.]+;\s*)', r'\1\nimport callreport.CallReport;\n', java_code)
        return modified_code
    
    # Save instrument_data as pickle in path.
    def save_instrumentdata(self, pkl_save_path):
        pickle.dump(self.instrument_data, open(pkl_save_path, "wb"))

# Replace None with empty string.
def non_none_str(str):
    return str if str != None else ""



# for test
if __name__ == "__main__":
    instrumenter = Instrumenter()
    instrumenter.instrument(sys.argv[1])