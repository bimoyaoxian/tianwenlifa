#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
司天学苑本地离线版 - 入口
"""
from calendar_engine.cli import run_cli, interactive
import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_cli()
    else:
        interactive()
