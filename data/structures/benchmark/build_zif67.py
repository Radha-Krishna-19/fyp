"""Build ZIF-67.cif from the project's ZIF-8.cif by replacing every Zn atom with Co.

ZIF-67, Co(2-methylimidazolate)2, is isostructural with ZIF-8, Zn(2-methylimidazolate)2: same sod net,
same space group I-43m, cell edge within about 0.3 % (ZIF-8 a = 16.99 A, ZIF-67 a = 16.96 A in the
literature). Only the metal changes. BFDH depends on the cell and the positions, not on the element,
so the BFDH shape of this file equals that of ZIF-8; the force-field surface energy changes with the
metal's UFF parameters. The file is therefore a built structure, not a measured one, and is labelled so.

Run:  python3 data/structures/benchmark/build_zif67.py
"""
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..', '..', 'website', 'ZIF-8.cif')
out = []
for line in open(SRC, encoding='utf-8'):
    # atom rows: label starting with Zn, and the type symbol column Zn
    line = re.sub(r'(?<![A-Za-z])Zn(?=\d|\s|$)', 'Co', line)
    out.append(line)
text = ''.join(out).replace('data_ZIF-8', 'data_ZIF-67_built_from_ZIF-8')
open(os.path.join(HERE, 'ZIF-67.cif'), 'w', encoding='utf-8').write(
    '# Built by data/structures/benchmark/build_zif67.py: ZIF-8.cif with every Zn replaced by Co.\n' + text)
print('wrote ZIF-67.cif')
