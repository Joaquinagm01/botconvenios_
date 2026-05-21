import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))
from backend.services.template_inspector import scan_templates
from backend.core.config import TEMPLATES_DIR

def main():
    mapping = scan_templates(Path(TEMPLATES_DIR))
    # Convert sets to lists for JSON
    out = {k: sorted(list(v)) for k, v in mapping.items()}
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
