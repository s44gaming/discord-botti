/**
 * Adds new language translations to i18n.js.
 * Uses English as fallback for new languages when no specific translation exists.
 * Run: node scripts/add-lang-i18n.js
 */
const fs = require('fs');
const path = require('path');

const NEW_LANGS = ['uk','ro','el','sk','he','fil','ms','bn'];

const i18nPath = path.join(__dirname, '../web/static/js/i18n.js');
let content = fs.readFileSync(i18nPath, 'utf8');

// Match each translation block: 'key': { ... }
// We need to add new languages before the closing };
const blockRegex = /'([^']+)':\s*\{([^}]+)\}/g;

content = content.replace(blockRegex, (match, key, inner) => {
  // Skip if already has uk (new langs already added)
  if (inner.includes("uk:'")) return match;

  // Extract en value
  const enMatch = inner.match(/en:'((?:[^'\\]|\\.)*)'/);
  const enVal = enMatch ? enMatch[1].replace(/\\/g, '\\\\').replace(/'/g, "\\'") : '';

  // Extract hi value (last lang before our addition)
  const hiMatch = inner.match(/hi:'((?:[^'\\]|\\.)*)'\s*$/);
  const hiVal = hiMatch ? hiMatch[1] : '';

  // Build additions for new languages - use en as fallback
  let add = '';
  for (const code of NEW_LANGS) {
    add += `, ${code}:'${enVal}'`;
  }

  // Replace hi:'xxx' at end with hi:'xxx', uk:'...', ...
  const newInner = inner.replace(/hi:'((?:[^'\\]|\\.)*)'\s*$/, (m) => m + add);
  return `'${key}': {${newInner}}`;
});

fs.writeFileSync(i18nPath, content);
console.log(`Added ${NEW_LANGS.join(', ')} to all translation keys. New languages use English as fallback.`);
