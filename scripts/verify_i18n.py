#!/usr/bin/env python3
"""Verify all i18n keys have all supported languages. Exit 1 if any missing."""
import re

I18N_PATH = 'web/static/js/i18n.js'
SUPPORTED = ['fi','en','de','fr','es','it','nl','pl','pt','ru','ja','zh','sv','nb','da','tr','ko','cs','hu','id','th','vi','ar','hi','uk','ro','el','sk','he','fil','ms','bn','sr','bg','hr','sl','lt','lv','et','fa','sw','af','ca','gl','ta','te','ml','ur','az','hy','ka','si','ne','my','km']

def main():
    with open(I18N_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    # Extract T object blocks: 'key': { ... }
    keys = re.findall(r"'([^']+)':\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}", content)
    missing = []
    for key, inner in keys:
        if not key.startswith(('index.','nav.','dash.','sect.','common.','feat.','gs.')) and 'label' not in key and 'desc' not in key:
            continue  # skip non-T entries
        for lang in SUPPORTED:
            if re.search(rf"\b{re.escape(lang)}:'", inner) is None:
                missing.append((key, lang))
    if missing:
        print("Missing translations:")
        for k, l in missing[:50]:
            print(f"  {k} missing {l}")
        if len(missing) > 50:
            print(f"  ... and {len(missing)-50} more")
        return 1
    print(f"OK: All {len([k for k,_ in keys if any(x in k for x in ['index','nav','dash','sect','common','feat','gs'])])} keys have all {len(SUPPORTED)} languages.")
    return 0

if __name__ == '__main__':
    exit(main())
