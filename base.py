# -*- coding: utf-8 -*-
"""
@File  : base.py
@Author: Sanbom
@Date  : 2022/12/21
@Desc  : 
"""
import json
import os.path
import re
import shutil
import time
from distutils.core import setup
from typing import Optional, Callable

# cythonize的导入必须为以下三行的末尾, 否则编译会出错
from setuptools.dist import Distribution
from setuptools.extension import Extension
from Cython.Build import cythonize

from constants import INPUT_DIR, BUILD_DIR, OUTPUT_DIR, BASE_DIR, DEFAULT_IGNORED_FILES, PROJECT_CONFIG_DIR


def get_files_of_directory(dir_abs_path: str, file_handler: Callable, package_handler: Callable,
                           ignore: dict = None, abandoned_files: list = None) -> str:
    """
    获取文件夹下的文件

    Args:

        dir_abs_path (str): 待遍历文件夹
        file_handler (callable): python文件处理方法
        package_handler (callable): python包处理方法
        ignore (dict): 文件/文件夹忽略规则
        abandoned_files (list): 不遍历的文件夹

    Returns:
        file_abs_path (str): 遍历的文件
    """
    if not os.path.exists(dir_abs_path):
        raise FileNotFoundError(dir_abs_path)

    for root, dirs, files in list(os.walk(dir_abs_path))[:1]:  # 只遍历顶级目录

        # 处理文件
        for file in files:
            if file.endswith('.c') or (file in abandoned_files):
                # 忽略.c文件以及隐藏文件
                continue

            file_abs_path = os.path.join(root, file)  # 绝对路径
            file_retrieve_path = file_abs_path.split(INPUT_DIR)[1]  # 相对路径(待编译项目的根目录)
            file_handler(file_retrieve_path)
            yield file_abs_path

        # 处理子目录
        for dir_ in dirs:
            if dir_ in abandoned_files:
                # 忽略文件夹
                continue

            dir_abs_path_ = os.path.join(root, dir_)  # 绝对路径
            dir_retrieve_path_ = dir_abs_path_.split(INPUT_DIR)[1]  # 相对路径(待编译项目的根目录)

            if package_handler(dir_retrieve_path_):
                results = get_files_of_directory(
                    dir_abs_path=dir_abs_path_, ignore=ignore,
                    abandoned_files=abandoned_files, file_handler=file_handler,
                    package_handler=package_handler)
                for file_abs_path in results:
                    yield file_abs_path


class FileCompilingFilterRulesParser(object):
    """
    文件是否编译规则的解析器

    # 编译忽略规则
    ignored_rules = dict(
                        type='ignored',
                        ignored_files=[
                            "xxx.py",
                            "/xxx/xxx.py",
                            ...
                        ],
                        ignored_packages=[
                            '/xxx',
                            '/xxx/xxx',
                            ...
                        ]
                    )

    # 保留编译规则
    reserved_rules = dict(
                            type='reserved',
                            reserved_files=[
                                "xxx.py",
                                "/xxx/xxx.py",
                                ...
                            ],
                            reserved_packages=[
                                '/xxx',
                                '/xxx/xxx',
                                ...
                            ]
                    )

    """
    RULE_TYPE_MAPPINGS = {
        'ignored': 'IGNORED',  # 不编译
        'reserved': 'RESERVED',  # 编译
    }

    def __init__(self, project_name: str, project_config: str):
        """
        Args:
            project_name (str): 项目名称
            project_config (str): 项目配置文件名称
        """
        project_config_file_path = os.path.join(PROJECT_CONFIG_DIR, project_config)
        if not os.path.exists(project_config_file_path):
            raise FileNotFoundError(project_config_file_path)

        self.project_config = json.load(open(project_config_file_path))

        self.rules = dict(
            IGNORED=dict(),
            RESERVED=dict()
        )

        self.type = None
        self.project_name = project_name

        ignored_rules = self.project_config.get('ignored_rules') or dict()
        reserved_rules = self.project_config.get('reserved_rules') or dict()

        if ignored_rules:
            self.type = self.RULE_TYPE_MAPPINGS['ignored']
            ignored_packages, ignored_files = ignored_rules.get('ignored_packages'), ignored_rules.get('ignored_files')
            self.rules[self.type]['ignored_files'] = self._preprocess_files_rules(ignored_files)
            self.rules[self.type]['ignored_packages'] = self._preprocess_packages_rules(ignored_packages,
                                                                                        self.rules[self.type][
                                                                                            'ignored_files'])

        elif reserved_rules:
            self.type = self.RULE_TYPE_MAPPINGS['reserved']
            reserved_packages, reserved_files = reserved_rules.get('reserved_packages'), reserved_rules.get(
                'reserved_files')
            self.rules[self.type]['reserved_files'] = self._preprocess_files_rules(reserved_files)
            self.rules[self.type]['reserved_packages'] = self._preprocess_packages_rules(reserved_packages,
                                                                                         self.rules[self.type][
                                                                                             'reserved_files'])

    def is_ignored_rules(self) -> bool:
        """是否为忽略编译类型"""
        return self.type == self.RULE_TYPE_MAPPINGS['ignored']

    def is_reserved_rules(self) -> bool:
        """是否为保留编译类型"""
        return self.type == self.RULE_TYPE_MAPPINGS['reserved']

    #######################################################
    #                       文件处理                       #
    #######################################################
    def _preprocess_files_rules(self, rules: list) -> list:
        """
        对文件匹配规则进行预处理

            待处理项目名称为django_server, 示例如下
                当匹配根目录下的py文件时, 将'/django_server/xxx.py'转为'django_server/xxx.py',被系统识别;
                当匹配非根目录的py文件时, '/test/xxx.py'可被系统识别,无需转换;

        Args:
            rules (list):

        Returns:
            rules (list):
        """
        results = list()
        for rule in rules:
            if rule.startswith('/{}'.format(self.project_name)):
                rule = rule[1:]
            results.append(rule)
        return results

    def is_ignored_file(self, name: str) -> bool:
        """是否为编译忽略的文件"""
        is_ignored = False
        if (not self.type) or (self.type != self.RULE_TYPE_MAPPINGS['ignored']):
            return is_ignored
        rules = self.rules[self.type]['ignored_files']
        for rule in rules:
            if re.search(rule, name):
                is_ignored = True
                break
        return is_ignored

    def is_reserved_file(self, name: str) -> bool:
        """是否为保留编译文件"""
        is_reserved = False
        if (not self.type) or (self.type != self.RULE_TYPE_MAPPINGS['reserved']):
            return is_reserved
        # 1.文件保留规则
        rules = self.rules[self.type]['reserved_files']
        for rule in rules:
            if re.search(rule, name):
                is_reserved = True
                break

        # 2.文件夹保留规则
        if not is_reserved:
            rules = self.rules[self.type]['reserved_packages']
            for rule in rules:
                if name.startswith(rule):
                    is_reserved = True
                    break

        return is_reserved

    #########################################################
    #                     python包处理                       #
    #########################################################
    def _preprocess_packages_rules(self, rules: list, files_rules: list) -> list:
        """
        对python包匹配规则进行预处理

            待处理项目名称为django_server, 示例如下
                当匹配根目录下的包时, 将'/django_server/xxx'转为'django_server/xxx',被系统识别;
                当匹配非根目录的包时, '/test/xxx'可被系统识别,无需转换;

        Args:
            rules (list):

        Returns:
            rules (list):
        """
        results = list()
        for rule in rules:
            if rule.startswith('/{}'.format(self.project_name)):
                rule = rule[1:]
            results.append(rule)

        # 只供指定文件夹下文件编译使用, 非编译整个文件夹
        self.reserved_package_rules_extend = list()
        for rule in files_rules:
            _ = list(rule.split('/'))
            if len(_) > 2:
                dir_ = '/'.join(_[:-1])
                self.reserved_package_rules_extend.append(dir_)

        return results

    def is_ignored_package(self, name: str) -> bool:
        """是否为编译忽略的文件夹"""
        is_ignored = False
        if (not self.type) or (self.type != self.RULE_TYPE_MAPPINGS['ignored']):
            return is_ignored
        name = name if name.endswith('/') else name + '/'
        rules = self.rules[self.type]['ignored_packages']
        for rule in rules:
            rule = rule if rule.endswith('/') else rule + '/'
            if re.search(rule, name):
                is_ignored = True
                break
        return is_ignored

    def is_reserved_package(self, name: str) -> bool:
        """是否为保留编译文件夹"""
        is_reserved = False
        if (not self.type) or (self.type != self.RULE_TYPE_MAPPINGS['reserved']):
            return is_reserved
        rules = self.rules[self.type]['reserved_packages'] + self.reserved_package_rules_extend

        for rule in rules:

            if rule.startswith('{}/'.format(name)):
                # 保留编译的父文件夹
                is_reserved = True
                break
            elif rule == name:
                # 待保留编译的文件夹
                is_reserved = True
                break
            elif name.startswith('{}/'.format(rule)):
                # 待保留编译文件夹的子文件夹
                is_reserved = True
                break

        return is_reserved


class PythonCodeCompilingBase(object):
    """Python代码编译"""
    # 默认忽略的文件/文件夹
    DEFAULT_IGNORED_FILES = DEFAULT_IGNORED_FILES

    def __init__(self, project_config: str, dir_path: str, no_cache: bool = False):
        """
        Args:
            dir_path (str):
            no_cache (bool): input目录是否保留上次拷贝的项目
        """
        self.source_dir = self._validate_dir(dir_path)
        self.no_cache = no_cache
        self.input_dir, self.out_dir, self.project_name = self._prepare_dirs()
        self.file_rule_parser: FileCompilingFilterRulesParser = FileCompilingFilterRulesParser(self.project_name,
                                                                                               project_config)
        self.build_lib_path = None

    def _validate_dir(self, dir_path: str) -> str:
        """
        校验待编码文件夹

        Args:
            dir_path (str):

        Returns:
            dir_path (str):
        """
        if os.path.exists(os.path.join(INPUT_DIR, dir_path)):
            return os.path.join(INPUT_DIR, dir_path)
        if os.path.exists(dir_path):
            return dir_path
        raise FileNotFoundError(dir_path)

    def _prepare_dirs(self) -> (str, str):
        """
        准备文件夹

        Returns:
            input_dir (str):
            output_dir (str):
        """
        dirname = self.source_dir.replace('\\', '/').split('/')[-1]

        # 1.复制源文件夹至输入目录下
        input_dir = os.path.join(INPUT_DIR, dirname)
        if not os.path.exists(input_dir):
            shutil.copytree(self.source_dir, input_dir)
            print("待编译文件夹已拷贝: [{}]".format(input_dir))
        else:
            if self.no_cache:
                shutil.rmtree(input_dir)
                shutil.copytree(self.source_dir, input_dir)
                print("待编译文件夹已拷贝: [{}]".format(input_dir))
            else:
                print("待编译文件夹已存在: [{}]".format(input_dir))

        # 2.清空整个编译文件夹
        if os.path.exists(BUILD_DIR):
            shutil.rmtree(BUILD_DIR)
            print("build文件夹已删除: [{}]".format(BUILD_DIR))

        # 3.删除并重新创建输出目录下该文件夹
        output_dir = os.path.join(OUTPUT_DIR, dirname)
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.mkdir(output_dir)
        print("编译后的输出文件夹已创建: [{}]".format(output_dir))

        return input_dir, output_dir, dirname

    def run(self):
        print()
        print(">" * 50)
        time_start = time.time()
        [file_abs_path for file_abs_path in get_files_of_directory(
            dir_abs_path=self.input_dir,
            abandoned_files=self.DEFAULT_IGNORED_FILES,
            file_handler=self.handle_file,
            package_handler=self.handle_package
        )]
        time_end = time.time()
        seconds_cost = time_end - time_start
        print()
        print(">" * 50)
        print("本次编译共耗时: {}".format(seconds_cost))
        print("结果输出文件夹: {}".format(os.path.join(self.out_dir)))

    ########################################
    #                文件处理               #
    ########################################

    def handle_file(self, name: str) -> None:
        """
        处理文件

        Args:
            name (str): 待处理文件

        Returns:

        """
        source_file = name
        so_file = None

        if (not self.is_python_file(name)) or name.endswith('__init__.py'):
            # 非python文件或者__init__.py文件, 跳过编译
            pass
        else:
            # python文件
            if self.file_rule_parser.is_ignored_rules():
                # 忽略编译
                if not self.is_ignored_file(name=name):
                    # 非忽略编译文件
                    so_file = self.py2so(name=name)
            elif self.file_rule_parser.is_reserved_rules():
                # 保留编译
                if self.is_reserved_file(name=name):
                    # 保留编译文件
                    so_file = self.py2so(name=name)
            else:
                # 直接编译
                so_file = self.py2so(name=name)

        if so_file:
            self.copy_so_file(so_file)
        elif source_file:
            self.copy_source_file(source_file)

        return None

    def is_ignored_file(self, name: str) -> bool:
        """
        是否为忽略编译文件

        Args:
            name (str): 待判断文件

        Returns:
            result (bool):
        """
        return self.file_rule_parser.is_ignored_file(name=name)

    def is_reserved_file(self, name: str) -> bool:
        return self.file_rule_parser.is_reserved_file(name=name)

    def is_python_file(self, name: str) -> bool:
        """
        是否为python文件

        Args:
            name (str): 待判断文件

        Returns:
            result (bool):
        """
        return name.endswith('.py')

    def py2so(self, name: str) -> str:
        """
        Python文件编译

        Args:
            name (str): 待处理文件

        Returns:
            so_file_name (str): 编译文件的相对路径
        """
        # 1.编译
        py_file_path = os.path.join(INPUT_DIR, name)
        dist_obj: Distribution = setup(
            script_args=['build_ext'],
            ext_modules=cythonize(
                py_file_path,
                compiler_directives={'always_allow_keywords': True}
            )
        )
        build_ext_obj = dist_obj.get_command_obj(command='build_ext')

        # 2.获取build/lib.xxx-cpython-xxx文件夹名称
        if not self.build_lib_path:
            build_lib = getattr(build_ext_obj, "build_lib")
            build_lib_path = os.path.join(BASE_DIR, build_lib)
            self.build_lib_path = build_lib_path

        # 3.获取编译后的so文件的相对路径
        extension_obj: Extension = getattr(build_ext_obj, 'extensions')[0]
        so_file_name = getattr(extension_obj, '_file_name')

        return so_file_name

    def copy_source_file(self, name: str) -> None:
        """
        拷贝源文件

        Args:
            name (str): 不编译的源文件

        Returns:

        """
        source_file = os.path.join(INPUT_DIR, name)
        target_file = os.path.join(OUTPUT_DIR, name)
        target_dir = os.path.dirname(target_file)
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        shutil.copyfile(source_file, target_file)

    def copy_so_file(self, name: str) -> None:
        """
        拷贝编译文件

        Args:
            name (str): 编译文件

        Returns:

        """
        source_file = os.path.join(self.build_lib_path, name)
        target_file = os.path.join(OUTPUT_DIR, name)
        target_dir = os.path.dirname(target_file)
        if not os.path.exists(target_dir):
            os.mkdir(target_dir)
        shutil.copyfile(source_file, target_file)

    ####################################################
    #                   python包处理                    #
    ####################################################
    def handle_package(self, name: str) -> Optional[str]:
        """
        处理python包

        Args:
            name (str): 待处理文件夹

        Returns:

        """
        source_dir = name
        package_dir = None

        if not self.is_python_package(name):
            # 非python包,跳过编译
            pass
        else:
            # python包
            if self.file_rule_parser.is_ignored_rules():
                # 忽略编译类型
                if not self.is_ignored_package(name=name):
                    # 非忽略编译python包
                    package_dir = name
            elif self.file_rule_parser.is_reserved_rules():
                # 保留编译类型
                if self.is_reserved_package(name=name):
                    # 保留编译python包
                    package_dir = name
            else:
                # 需要编译的python包
                package_dir = name

        if package_dir:
            return name
        elif source_dir:
            self.copy_source_dir(source_dir)
            return None
        return None

    def is_python_package(self, name: str) -> bool:
        """
        是否为python包

        Args:
            name (str): 待判断文件夹

        Returns:
            result (bool):
        """
        files = os.listdir(os.path.join(INPUT_DIR, name))
        return '__init__.py' in files

    def is_ignored_package(self, name: str) -> bool:
        return self.file_rule_parser.is_ignored_package(name=name)

    def is_reserved_package(self, name: str) -> bool:
        return self.file_rule_parser.is_reserved_package(name=name)

    def copy_source_dir(self, source_dir: str) -> None:
        """
        拷贝源文件夹

        Args:
            source_dir (str): 源文件夹

        Returns:

        """
        source_dir_abs_path = os.path.join(INPUT_DIR, source_dir)
        target_dir = os.path.join(OUTPUT_DIR, source_dir)
        target_parent_dir = os.path.dirname(target_dir)
        if not os.path.exists(target_parent_dir):
            os.mkdir(target_parent_dir)
        shutil.copytree(source_dir_abs_path, target_dir)
