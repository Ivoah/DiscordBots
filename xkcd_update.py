#!/bin/sh
"exec" "`dirname $0`/venv/bin/python" "$0" "$@"

import json
import requests

comics = {}

latest = requests.get('http://xkcd.com/info.0.json').json()['num']

for i in range(1, latest + 1):
    print(f'\rUpdating xkcd database: {i}/{latest} ({i/latest*100:.2f}%)', end='')
    if i == 404: continue
    comics[i] = requests.get(f'http://xkcd.com/{i}/info.0.json').json()
print()

with open('xkcd.json', 'w') as f:
    json.dump(comics, f)
