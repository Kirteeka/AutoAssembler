import re
from flask import Flask, request, send_from_directory, jsonify
import subprocess

app = Flask(__name__, static_folder="frontend")

@app.route('/')
def home():
    return send_from_directory('frontend', 'index.html')

@app.route('/compile', methods=['POST'])
def compile_code():
    data = request.get_json()
    with open("input.c", "w") as f:
        f.write(data["source"])
    try:
        result = subprocess.run(
            ["ICG/icg.exe"],
            stdin=open("input.c"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        output = result.stdout or result.stderr

        # Clean ANSI escape codes
        ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
        clean_output = ansi_escape.sub('', output)

        # Extract sections
        asm_code = []
        symbol_table = []
        constant_table = []
        parse_tree = []

        section = None
        for line in clean_output.splitlines():
            if "func begin" in line or line.startswith("t") or line.startswith("func end"):
                section = "asm"
            elif "SYMBOL TABLE" in line:
                section = "sym"
            elif "CONSTANT TABLE" in line:
                section = "const"
            elif "Parse Tree" in line or "Tree" in line:
                section = "tree"
            elif "Status: Parsing" in line:
                section = None  # End of sections

            if section == "asm":
                asm_code.append(line)
            elif section == "sym":
                symbol_table.append(line)
            elif section == "const":
                constant_table.append(line)
            elif section == "tree":
                parse_tree.append(line)

        return jsonify({
            "assembly": "\n".join(asm_code),
            "symbol_table": "\n".join(symbol_table),
            "constant_table": "\n".join(constant_table),
            "parse_tree": "\n".join(parse_tree)
        })

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)