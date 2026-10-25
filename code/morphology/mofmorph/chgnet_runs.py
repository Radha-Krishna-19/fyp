"""
chgnet_runs.py: access to the CHGNet (MorphoGraph-MOF notebook) result folders.

The notebook writes one results folder per MOF. The project keeps them, unpacked, in
    data/chgnet_morphograph_runs/<MOF>_<run date>/        e.g.  MOF-5_2026-10-14/
Each folder holds the bulk cells, the initial and relaxed slabs, the per-slab energies
(*_surface_energies_individual.csv), the pair-fit summary (*_surface_pair_fit_summary.csv),
the metadata (*_metadata.json) and two reference particles.

RunFolder offers the small part of the zipfile.ZipFile interface that the analysis scripts
use (namelist, read, open, extractall), so the same code reads a results folder or, if one
is passed explicitly, the original zip downloaded from Colab.
"""
import glob
import io
import os
import shutil
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "data", "chgnet_morphograph_runs"))


class RunFolder:
    """A CHGNet results folder with a zipfile-like interface."""

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.label = os.path.basename(self.path)               # e.g. MOF-5_2026-10-14
        self.mof = self.label.rsplit("_", 1)[0]                  # e.g. MOF-5

    def namelist(self):
        out = []
        for root, _dirs, files in os.walk(self.path):
            for f in files:
                out.append(os.path.relpath(os.path.join(root, f), self.path).replace(os.sep, "/"))
        return sorted(out)

    def read(self, name):
        with open(os.path.join(self.path, name), "rb") as fh:
            return fh.read()

    def open(self, name):
        return io.BytesIO(self.read(name))

    def extractall(self, target):
        shutil.copytree(self.path, target, dirs_exist_ok=True)

    def __repr__(self):
        return f"RunFolder({self.label})"


def runs(mof=None):
    """All CHGNet result folders (optionally only one MOF), sorted by name."""
    out = [RunFolder(p) for p in sorted(glob.glob(os.path.join(RUNS_DIR, "*"))) if os.path.isdir(p)]
    return [r for r in out if mof is None or r.mof == mof]


def open_archive(path):
    """A RunFolder for a folder, or a zipfile.ZipFile for a zip downloaded from Colab."""
    return RunFolder(path) if os.path.isdir(path) else zipfile.ZipFile(path)
