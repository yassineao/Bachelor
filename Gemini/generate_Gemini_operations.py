import ast
import os
from pathlib import Path
import google.generativeai as genai

api_key = os.environ.get("GENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the GENAI_API_KEY environment variable.")
genai.configure(api_key)

SOURCE_FILE = "./tinydb/operations.py"
OUTPUT_DIR = "tests/generated"
OUTPUT_FILE = "test_operations_methods.py"

os.makedirs(OUTPUT_DIR, exist_ok=True)
with open(SOURCE_FILE, "r", encoding="utf-8") as f:
    source_code = f.read()

tree = ast.parse(source_code)
public_funcs = [
    fn for fn in tree.body
    if isinstance(fn, ast.FunctionDef) and not fn.name.startswith("_")
]

def get_source_segment(node):
    return ast.get_source_segment(source_code, node)

model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
all_tests = ""

for fn in public_funcs:
    name = fn.name
    code = get_source_segment(fn)

    prompt = f""" Write pytest unit tests for this function from TinyDB's operations module:

Function:
{code}

Test the returned transformer: e.g. apply to a sample document (dict), call it, and assert the modified document. Cover edge cases.
Only return test code.
"""
    print(f" Generating test for: {name}")
    resp = model.generate_content(prompt)
    all_tests += f"\n\n# === Tests for `{name}` ===\n{resp.text.strip()}"

out = Path(OUTPUT_DIR) / OUTPUT_FILE
out.write_text(all_tests.strip(), encoding="utf-8")
print(f"✅ Tests saved to {out}")
