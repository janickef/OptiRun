import os
import shutil
import sys
from ConfigParser import SafeConfigParser
import socket

dirs = ['linux', 'windows']
section = 'CONFIG'

for item in dirs:
    src = os.path.join(sys.path[0], '..', 'node', item)
    config_path = os.path.join(src, 'config.ini')

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))

    config = SafeConfigParser()
    config.read(config_path)

    if section not in config.sections():
        config.add_section(section)

    config.set(section, 'port', 5555)
    config.set(section, 'hub_host', socket.gethostname())
    config.set(section, 'hub_ip', s.getsockname()[0])

    with open(config_path, 'w') as f:
        config.write(f)

    shutil.make_archive(item, 'zip', os.path.join(sys.path[0], '..', 'node', item))
    shutil.copy(
        os.path.join(sys.path[0], '%s.zip' % item),
        os.path.join(sys.path[0], '..', '..', 'files')
    )
    os.remove('%s.zip' % item)
