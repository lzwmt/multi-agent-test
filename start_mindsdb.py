#!/usr/bin/env python3
"""Start MindsDB server"""

import sys
import os

# Add mindsdb to path
sys.path.insert(0, '/usr/local/lib/python3.11/dist-packages')

if __name__ == '__main__':
    sys.argv = ['mindsdb', '--api', 'http']
    # Execute mindsdb.__main__ as a script
    exec(open('/usr/local/lib/python3.11/dist-packages/mindsdb/__main__.py').read())
