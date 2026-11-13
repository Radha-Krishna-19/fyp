"""Write website/default_cif_data.js: the CIF files the browser pages load without an upload.

The four cubic demonstration structures come first (website/*.cif), then eight more chosen to
differ in metal, node, linker and lattice (data/structures/general_lattice/, see its README).
The Overview and Network pages run their live tables on every structure listed here.

Run:  python3 website/_build/build_default_cifs.py
"""
import os, json
HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, '..'))
GEN = os.path.join(SITE, '..', 'data', 'structures', 'general_lattice')
FILES = [('HKUST-1', os.path.join(SITE, 'HKUST-1.cif')), ('UiO-66', os.path.join(SITE, 'UiO-66.cif')),
         ('MOF-5', os.path.join(SITE, 'MOF5.cif')), ('ZIF-8', os.path.join(SITE, 'ZIF-8.cif')),
         ('ZIF-7', os.path.join(GEN, 'ZIF-7.cif')), ('MOF-177', os.path.join(GEN, 'MOF-177.cif')),
         ('DMOF-1', os.path.join(GEN, 'DMOF-1.cif')), ('MIL-88A', os.path.join(GEN, 'MIL-88A-open.cif')),
         ('Mg-MOF-74', os.path.join(GEN, 'MgMOF-74.cif')), ('MIL-53(Cr)', os.path.join(GEN, 'MIL-53Cr-lt.cif')),
         ('MIL-47(V)', os.path.join(GEN, 'MIL-47.cif')), ('MIL-140A', os.path.join(GEN, 'MIL-140A.cif'))]
with open(os.path.join(SITE, 'default_cif_data.js'), 'w', encoding='utf-8') as f:
    f.write('window.DEFAULT_CIFS = {\n')
    f.write(',\n'.join('  %s: %s' % (json.dumps(k), json.dumps(open(p, encoding='utf-8').read())) for k, p in FILES))
    f.write('\n};\n')
print('wrote default_cif_data.js with', len(FILES), 'structures')
