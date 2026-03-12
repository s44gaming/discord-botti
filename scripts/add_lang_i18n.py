#!/usr/bin/env python3
"""Add new languages to all i18n keys. Uses English as fallback.
Run: python scripts/add_lang_i18n.py
"""
import re

# New languages: add after last existing (bn). Uses en as fallback for consistency.
NEW_LANGS = ['sr','bg','hr','sl','lt','lv','et','fa','sw','af','ca','gl','ta','te','ml','ur','az','hy','ka','si','ne','my','km']
I18N_PATH = 'web/static/js/i18n.js'

def process_line(line):
    # Skip if already has first new lang
    if any(f"{lang}:'" in line for lang in NEW_LANGS[:1]):
        return line
    if 'bn:' not in line or "': {" not in line:
        return line
    en_m = re.search(r"en:'((?:[^'\\]|\\.)*)'", line)
    if not en_m:
        return line
    en_val = en_m.group(1).replace("\\'", "'").replace("\\\\", "\\")
    en_escaped = en_val.replace("\\", "\\\\").replace("'", "\\'")
    additions = ''.join(f", {lang}:'{en_escaped}'" for lang in NEW_LANGS)
    new_line = re.sub(r"(bn:'(?:[^'\\]|\\.)*')\s*(\})", r"\1" + additions + r" \2", line)
    return new_line

def main():
    with open(I18N_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    out = []
    changed = 0
    for line in lines:
        new_line = process_line(line)
        if new_line != line:
            changed += 1
        out.append(new_line)
    with open(I18N_PATH, 'w', encoding='utf-8') as f:
        f.writelines(out)
    print(f"Added {len(NEW_LANGS)} languages to {changed} keys (English fallback).")

if __name__ == '__main__':
    main()
