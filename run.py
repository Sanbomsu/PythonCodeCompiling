# -*- coding: utf-8 -*-
"""
@File  : run.py
@Author: Sanbom
@Date  : 2022/12/21
@Desc  :
"""
import time

import click

from base import PythonCodeCompilingBase


@click.command()
@click.argument('dir_path', nargs=1)
@click.argument('project_config', nargs=1)
@click.option('--cache/--no-cache', default=False, help="是否使用缓存")
def python_code_compiling_tool(dir_path: str, project_config: str, cache: bool):
    """
    python代码编译工具

        dir_path (str): 待编译python项目路径, 该文件夹必须为Python包,即包含__init__.py, 否则build中该项目目录结构混乱\n

        project_config (str): 待编译项目的编译规则json, 位于projects_config目录下\n
        cache (bool): 是否用缓存项目文件, 默认False, 即利用input文件下上次复制的项目文件, 加速编译\n

        注:\n
        1.python项目名称必须符合Python变量命名规则\n
        2.python函数的返回类型注解不对, 会导致编译出错, 示例如下:\n

            # 编译报错
            def test() -> (list, dict):
                pass

            # 编译通过
            from typing import List,Dict
            def test() -> (List, Dict):
                pass

    """
    PythonCodeCompilingBase(
        dir_path=dir_path,
        project_config=project_config,
        no_cache=not cache,
    ).run()
    print('60秒后自动退出')
    time.sleep(60)


if __name__ == '__main__':
    python_code_compiling_tool()
