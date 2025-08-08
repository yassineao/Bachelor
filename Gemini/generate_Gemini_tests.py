import ast
import os
from pathlib import Path
import google.generativeai as genai

api_key = os.environ.get("GENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the GENAI_API_KEY environment variable.")
genai.configure(api_key)

SOURCE_FILE = "./tinydb/database.py"
OUTPUT_DIR = "tests/generated"
OUTPUT_FILE = "test_tinydb_methods.py"
CLASS_NAME = "TinyDB"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(SOURCE_FILE, "r") as f:
    source_code = f.read()

tree = ast.parse(source_code)

class_def = next(
    (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == CLASS_NAME),
    None
)

if class_def is None:
    raise ValueError(f"Class '{CLASS_NAME}' not found in {SOURCE_FILE}")

public_methods = [
    node for node in class_def.body
    if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
]

def get_source_segment(node: ast.FunctionDef) -> str:
    return ast.get_source_segment(source_code, node)

model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")

all_tests = ""

for method in public_methods:
    method_name = method.name
    method_code = get_source_segment(method)

    prompt = f"""
 Write **pytest-based** unit tests for this method from TinyDB's Table class.

Use mocking for dependencies like `self._storage`. Focus on correctness and edge cases.

Only return test code. No explanation.

Method:
{method_code}
"""

    print(f" Generating test for: {method_name}")
    response = model.generate_content(prompt)

    test_code = response.text.strip()

    all_tests += f"\n\n# === Tests for `{method_name}` ===\n{test_code}"

output_path = Path(OUTPUT_DIR) / OUTPUT_FILE
with open(output_path, "w", encoding="utf-8") as f:
    f.write(all_tests.strip())

print(f"✅ All tests saved to {output_path}")
