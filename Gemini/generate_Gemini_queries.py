import ast
import os
from pathlib import Path
import google.generativeai as genai

api_key = os.environ.get("GENAI_API_KEY")
if not api_key:
    raise ValueError("Please set the GENAI_API_KEY environment variable.")
genai.configure(api_key)

SOURCE_FILE = "./tinydb/queries.py"
OUTPUT_DIR = "tests/generated"
OUTPUT_FILE = "test_query_methods.py"
CLASS_NAMES = ["QueryInstance", "Query"]

os.makedirs(OUTPUT_DIR, exist_ok=True)

source_code = open(SOURCE_FILE, "r", encoding="utf-8").read()
tree = ast.parse(source_code)

model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
all_tests = ""

def get_methods_for_class(class_def):
    return [
        m for m in class_def.body
        if isinstance(m, ast.FunctionDef) and not m.name.startswith("_")
    ]

def get_source_segment(node):
    return ast.get_source_segment(source_code, node)

for class_name in CLASS_NAMES:
    class_def = next(
        (n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name),
        None
    )
    if not class_def:
        print(f"⚠️ Class {class_name} not found — skipping.")
        continue

    methods = get_methods_for_class(class_def)
    for method in methods:
        method_name = method.name
        code = get_source_segment(method)
        prompt = f""" Write pytest unit tests for this method of TinyDB's {class_name} class.

Use temporary files or in-memory mocks for file operations where applicable.
Only return test code. No explanations.

Method:
{code}
"""
        print(f" Generating test for: {method_name}")
        response = model.generate_content(prompt)

        test_code = response.text.strip()

        all_tests += f"\n\n# === Tests for `{method_name}` ===\n{test_code}"

output_path = Path(OUTPUT_DIR) / OUTPUT_FILE
with open(output_path, "w", encoding="utf-8") as f:
    f.write(all_tests.strip())

print(f"✅ All tests saved to {output_path}")

