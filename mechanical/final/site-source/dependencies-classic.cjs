// Exercise the exact embedded v27 Three.js / LDraw libraries without downloads.
const fs = require('node:fs');
const path = require('node:path');
const library = JSON.parse(fs.readFileSync(path.join(__dirname, 'native-presentation.json'))).library;
module.exports = new Function(library + '\nreturn {THREE, LDrawLoader, LDrawConditionalLineMaterial};')();
