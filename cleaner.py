#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os

directory = os.path.dirname(sys.argv[0])
files = os.listdir(directory)
[os.remove(file) for file in files if file.endswith('.txt')]
