const path = require('path');
const SITE = path.join(__dirname, '..');
const fs = require('fs');
const { parseCIF, buildStructure } = require(path.join(SITE,'mof_decompose.js'));

const text = fs.readFileSync(path.join(SITE,'HKUST-1.cif'), 'utf8');
const parsed = parseCIF(text);
console.log('Parsed atoms:', parsed.atoms.length, 'cellPar:', parsed.cellPar.map(x=>+x.toFixed(3)));

const DATA = buildStructure(parsed.atoms, parsed.cellMatrix);
console.log('n_atoms:', DATA.n_atoms);
console.log('n_metal_blocks:', DATA.n_metal_blocks, 'n_linker_blocks:', DATA.n_linker_blocks);
console.log('metal block sizes:', DATA.blocks.filter(b=>b.type==='metal').map(b=>b.n_atoms));
console.log('linker block sizes:', DATA.blocks.filter(b=>b.type==='linker').map(b=>b.n_atoms));
console.log('total bonds:', DATA.bonds.length);
console.log('formula:', DATA.formula);
