import re
import os

org = '<svg version="1.1"'

for root, dirs, files in os.walk(".", topdown=False):
    for name in files:
        if not name.endswith('.svg'):
            continue

        with open(name, 'r+') as f:
            content = f.read()

        class_name = 'linearicon icon-{}'.format(name[:-4])
        sub = '{} class="{}"'.format(org, class_name)
        new_content = re.sub(org, sub, content)

        with open(name, 'w+') as f:
            f.write(new_content)
