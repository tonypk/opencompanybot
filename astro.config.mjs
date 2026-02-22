{
  "$schema": "https://astro.build/config/astro.schema.json",
  "src": "./web/src",
  "public": "./web/public",
  "output": "static",
  "build": {
    "format": "file"
  },
  "integrations": [],
  "i18n": {
    "defaultLocale": "en",
    "locales": ["en", "zh"],
    " routing": {
      "prefixDefaultLocale": false
    }
  }
}
