# -*- coding: utf-8 -*-
"""
@File  : constants.py
@Author: Sanbom
@Date  : 2022/12/21
@Desc  : 
"""
import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, 'input/')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output/')
BUILD_DIR = os.path.join(BASE_DIR, 'build/')
PROJECT_CONFIG_DIR = os.path.join(BASE_DIR, 'projects_config/')

# 默认忽略的文件/文件夹
DEFAULT_IGNORED_FILES = [
    '.git',
    '.idea',
    '__pycache__',
    '.DS_Store',
    'migrations',  # django数据库迁移文件, 无法编译
]
