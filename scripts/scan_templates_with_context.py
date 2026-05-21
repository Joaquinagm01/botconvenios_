import json
from pathlib import Path
import sys
import re

sys.path.insert(0, str(Path.cwd()))
from backend.services.template_inspector import extract_placeholders_from_docx
from docx import Document
from backend.core.config import TEMPLATES_DIR
import zipfile
import html

PLACEHOLDER_RE = re.compile(r"\{\{\s*([^\}]+)\s*\}\}")

def contexts_for_docx(path: Path):
    contexts = {}
    # try to get plain paragraph contexts first
    try:
        doc = Document(path)
        for p in doc.paragraphs:
            for m in PLACEHOLDER_RE.findall(p.text):
                key = m.strip()
                contexts.setdefault(key, []).append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for m in PLACEHOLDER_RE.findall(cell.text):
                        key = m.strip()
                        contexts.setdefault(key, []).append(cell.text.strip())
    except Exception:
        pass

    # fallback: inspect document.xml raw for occurrences of variable names
    try:
        with zipfile.ZipFile(path, 'r') as z:
            xml = z.read('word/document.xml').decode('utf-8', errors='ignore')
            for key in list(contexts.keys()):
                # already have contexts
                continue
            # if no contexts found, try to find any alphanumeric tokens from xml like ${var} or numeric tokens
            tokens = set(re.findall(r"\$\{?([A-Za-z0-9_\-]+)\}?|\{\{\s*([^\}]+)\s*\}\}|<<\s*([A-Za-z0-9_\-]+)\s*>>|([0-9]{1,4})", xml))
            # tokens is a set of tuples; flatten
            flat = set()
            for t in tokens:
                for g in t:
                    if g:
                        flat.add(g)
            for tok in flat:
                idx = xml.find(tok)
                if idx != -1:
                    start = max(0, idx - 60)
                    end = min(len(xml), idx + len(tok) + 60)
                    snippet = xml[start:end]
                    # strip tags for readability
                    snippet = re.sub(r'<[^>]+>', ' ', snippet)
                    snippet = ' '.join(snippet.split())
                    contexts.setdefault(tok, []).append(snippet)
    except Exception:
        pass

    return contexts

def main():
    out = {}
    templates_dir = Path(TEMPLATES_DIR)
    for p in sorted(templates_dir.glob('*.docx')):
        placeholders = extract_placeholders_from_docx(p)
        ctxt = contexts_for_docx(p)
        out[p.name] = {"placeholders": sorted(list(placeholders)), "contexts": ctxt}
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
