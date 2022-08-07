import os
import shutil
from pathlib import Path


def submit():
    shutil.rmtree(Path(__file__).parent / 'dist')
    version = 'patch'
    os.system(f'poetry version {version}')
    os.system(f'poetry publish --build -r panhaoyu')
    os.system(f'git add "pyproject.toml"')
    os.system(f'git commit -m "new {version} version"')
    os.system('git push')


if __name__ == '__main__':
    submit()
