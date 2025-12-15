#!/usr/bin/env python3
"""Helper script to run docker-compose."""

import subprocess
import os

os.chdir(r'C:\Users\arbuz\Desktop\bots\miniapp_T')
subprocess.run(['docker-compose', 'up'], check=True)
