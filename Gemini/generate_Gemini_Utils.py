import ast
import os
from pathlib import Path
import google.generativeai as genai

api_key = os.environ.get("GENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the GENAI_API_KEY environment variable.")
genai.configure(api_key)

SOURCE_FILE = "./tinydb/utils.py"
OUTPUT_DIR = "tests/generated"
OUTPUT_FILE = "test_utils_methods.py"

TARGETS = ["with_typehint", "LRUCache", "FrozenDict", "freeze"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    source_code = f.read()
tree = ast.parse(source_code)

definitions = [
    node for node in tree.body
    if (isinstance(node, ast.FunctionDef) and node.name in TARGETS)
    or (isinstance(node, ast.ClassDef) and node.name in TARGETS)
]

if not definitions:
    raise ValueError("No target definitions found in utils.py")

def get_segment(node):
    return ast.get_source_segment(source_code, node)

model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")

all_tests = ""
for node in definitions:
    method_name = node.name
    code = get_segment(node)
    prompt = f"""write unit tests using pytest for the TinyDB utils module.
Generate tests for `{method_name}` based on this implementation:

```python
{code}"""
    print(f" Generating test for: {method_name}")
    response = model.generate_content(prompt)

    test_code = response.text.strip()

    all_tests += f"\n\n# === Tests for `{method_name}` ===\n{test_code}"

output_path = Path(OUTPUT_DIR) / OUTPUT_FILE
with open(output_path, "w", encoding="utf-8") as f:
    f.write(all_tests.strip())

print(f"✅ All tests saved to {output_path}")
