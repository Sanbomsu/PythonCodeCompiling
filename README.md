# 1. 功能介绍
---
该脚本可以有选择性地, 将待处理python项目中py文件进行编译, 生成的`.so`文件可实现类加密目的.
>注意: 编译所用python版本以及系统类型, 必须与运行环境保持一致. 
>例如,  同为`linux`内核的`python3.7`, 才能正常运行编译好的`xxx.cpython-37m-x86_64-linux-gnu.so`文件.

# 2. 目录结构
---
```bash
.  
|____input  # 输入文件夹
|____output  # 输出文件夹
|____projects_config  # 项目编译规则
| |____demo.json  # 单个项目的编译规则
|____base.py  # 基础文件
|____constants.py  # 全局变量; 其中DEFAULT_IGNORED_FILES, 可自行定义文件遍历时, 忽略文件夹或无法编译的python包
|____run.py  # 入口文件
|____requirements.txt  
|____README.md

```

# 3. 使用说明
---
## 3.1 运行
---
命令行模式启动项目编译: `python run.py <your_project_path> <your_project_config>.json --no-cache`
输入结果如下:
```shell
(xxx) ➜  PythonCodeCompiling python run.py /xxx/xxx xxx.json      
待编译文件夹已拷贝: [/xxx/PythonCodeCompiling/input/xxx]
编译后的输出文件夹已创建: [/xxx/PythonCodeCompiling/output/xxx]
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
[1/1] Cythonizing /Users/xxx/Storage/MyCode/PythonCodeCompiling/input/xxx/mixins.py
/Users/xxx/.virtualenvs/PythonCodeCompiling/lib/python3.7/site-packages/Cython/Compiler/Main.py:369: FutureWarning: Cython directive 'language_level' not set, using 2 for now (Py2). This will change in a later release! File: /Users/xxx/Storage/MyCode/PythonCodeCompiling/input/django_server/mixins.py
  tree = Parsing.p_module(s, pxd, full_module_name)
Compiling /Users/xxx/Storage/MyCode/PythonCodeCompiling/input/django_server/runner.py because it changed.
...
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
本次编译共耗时: 178.13617205619812
结果输出文件夹: /xxx/PythonCodeCompiling/output/xxx
60秒后自动退出
```

## 3.2 参数说明
---
### 3.2.1 dir_path
待编译python项目路径, 要求如下: 
- 该文件夹必须为python包, 即包含`__init__.py`, 否则会导致编译输出的目录结构混乱;
- 该文件夹名称, 必须符合Python变量命名规则, 否则编译报错; 
>注: python函数的返回类型注解不对时, 会导致编译出错, 示例如下: 

```python
# 编译报错  
def test() -> (list, dict):        
	pass  

# 编译通过  
from typing import List,Dict    
def test() -> (List, Dict):
	pass
```
### 3.2.2 project_config
项目的编译规则文件名称, 位于`projects_config`目录下;
- 规则类型(二选一)
	- 忽略编译
	- 保留编译
#### 3.2.2.1 忽略编译
在该模式下, 会忽指定文件和文件夹下文件的编译, 适用于`编译项目中的大量文件, 而忽略少部分文件`的场景.
```json
{
    "ignored_rules": {  
        "type": "ignored",  
        "ignored_files": [  
            "a.py",  // 单个文件名称
            "/b/c.py", // 相对某个文件夹的单个文件名称
            "/project_name/d/e.py"  // 相对于项目根目录的单个文件名称
        ],  
        "ignored_packages": [  
            "/a",  // 单个文件夹
            "/b/c",  // 相对某个文件夹的单个文件夹
            "/project_name/d/e" // 相对于项目根目录的单个文件夹名称
        ]  
    } 
}
```
#### 3.2.2.2 保留编译
在该模式下, 只会编译指定文件和文件夹下文件, 适用于`编译项目中的少量文件, 而忽略大部分文件`的场景.
```json
{
    "reserved_rules": {  
        "type": "reserved",  
        "reserved_files": [  
            "/project_name/a.py" // 相对于项目根目录的单个文件名称 
            "/project_name/b/c.py" // 相对于项目根目录的单个文件名称 
        ],  
        "reserved_packages": [  
            "/project_name/a",  // 相对于项目根目录的单个文件夹名称
            "/project_name/b/c"  // 相对于项目根目录的单个文件夹名称
        ]  
    } 
}
```
### 3.2.3 cache
是否用缓存项目文件, 默认`False`, 即利用input文件下上次复制的项目文件, 加速编译.