#!/usr/bin/env python3
"""Clear all outputs from a Jupyter notebook file."""

import json
import sys
from pathlib import Path

def clear_notebook_outputs(notebook_path):
    """Clear all outputs from a Jupyter notebook."""
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    # Clear outputs from all cells
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None

    # Save the cleaned notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"✓ Cleared all outputs from {notebook_path}")

if __name__ == '__main__':
    notebook_file = Path(__file__).parent / 'src' / 'agents' / 'main' / 'main_agent.ipynb'
    clear_notebook_outputs(notebook_file)