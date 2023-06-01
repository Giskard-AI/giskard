import os
import re
import sys
from pathlib import Path

if __name__ == '__main__':
    out_relative_path = sys.argv[1]
    fix_string = sys.argv[2]
    generated_dir = Path(os.getcwd()) / out_relative_path
    for dirpath, dirs, files in os.walk(generated_dir):
        for filename in files:
            if not filename.endswith('.py'):
                continue
            fname = os.path.join(dirpath, filename)
            with open(fname) as rfile:
                content = rfile.read()
                content = re.sub(
                    '^import ([^\\. ]*?_pb2)', f'import {fix_string}.\g<1>',
                    content, flags=re.MULTILINE)
                with open(fname, 'w') as wfile:
                    wfile.write(content)
                print(f'Fixed {fname}')
