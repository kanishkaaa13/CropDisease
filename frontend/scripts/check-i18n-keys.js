const fs = require("fs");
const path = require("path");

const messagesDir = path.join(__dirname, "..", "messages");
const locales = ["en", "hi", "mr"];
const catalogs = Object.fromEntries(
  locales.map((locale) => [locale, JSON.parse(fs.readFileSync(path.join(messagesDir, `${locale}.json`), "utf8"))])
);

function flatten(value, prefix = "") {
  return Object.entries(value).reduce((keys, [key, child]) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (child && typeof child === "object" && !Array.isArray(child)) {
      return keys.concat(flatten(child, fullKey));
    }
    return keys.concat(fullKey);
  }, []);
}

const sourceKeys = flatten(catalogs.en);
let failures = 0;

for (const locale of locales.slice(1)) {
  const targetKeys = new Set(flatten(catalogs[locale]));
  for (const key of sourceKeys) {
    const value = key.split(".").reduce((current, part) => current?.[part], catalogs[locale]);
    if (!targetKeys.has(key) || typeof value !== "string" || !value.trim()) {
      console.error(`${locale}: missing or empty key ${key}`);
      failures += 1;
    }
  }
}

if (failures > 0) {
  process.exitCode = 1;
} else {
  console.log(`i18n key check passed: ${sourceKeys.length} keys across ${locales.join(", ")}`);
}
