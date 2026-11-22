"""MkDocs hooks for the site (mkdocs.yml `hooks`): after the build, the
dictionaries the Font page's converter loads are copied to
site/assets/lexicon/ from data/lexicon/, where they are kept once."""
import glob
import os
import shutil


def on_post_build(config, **kwargs):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(config['site_dir'], 'assets', 'lexicon')
    os.makedirs(out, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(root, 'data', 'lexicon', '*.json'))):
        shutil.copyfile(path, os.path.join(out, os.path.basename(path)))
