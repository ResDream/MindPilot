# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(SPEC))
src_dir = os.path.join(current_dir, 'src', 'mindpilot')

# 获取所有需要包含的hiddenimports
hiddenimports = []
hiddenimports.extend(collect_submodules('langchain'))
hiddenimports.extend(collect_submodules('fastapi'))
hiddenimports.extend(collect_submodules('uvicorn'))
hiddenimports.extend(collect_submodules('starlette'))
hiddenimports.extend(collect_submodules('pydantic'))
hiddenimports.extend(collect_submodules('openai'))
# 添加mindnlp相关
hiddenimports.extend(collect_submodules('mindnlp'))
hiddenimports.extend(collect_submodules('mindnlp.transformers'))
hiddenimports.extend(['sqlite3', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
                    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
                    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
                    'uvicorn.lifespan', 'uvicorn.lifespan.on', 'email.mime.text'])

# 添加需要排除的包
excludes = ['matplotlib', 'tkinter', 'PySide6', 'PyQt5', 'PyQt6', 'notebook']

# 收集数据文件
datas = []
# 添加mindnlp的数据文件
datas.extend(collect_data_files('mindnlp'))
datas.extend(collect_data_files('mindnlp.transformers'))

# 添加cache目录
cache_dir = os.path.join(current_dir, 'cache')
if os.path.exists(cache_dir):
    datas.extend([(cache_dir, 'cache')])

# 添加数据库文件
db_file = os.path.join(src_dir, 'mindpilot.db')
if os.path.exists(db_file):
    datas.extend([(db_file, '.')])

# 添加knowledge_base目录
kb_dir = os.path.join(src_dir, 'knowledge_base')
if os.path.exists(kb_dir):
    datas.extend([(kb_dir, 'knowledge_base')])

# 添加其他必要的数据文件
datas.extend(collect_data_files('mindnlp', include_py_files=True))

# 收集动态链接库
binaries = []
binaries.extend(collect_dynamic_libs('mindnlp'))

a = Analysis(
    [os.path.join(src_dir, 'main.py')],
    pathex=[src_dir],
    binaries=binaries,  # 添加收集的动态链接库
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 删除一些不需要的模块的数据文件
def remove_from_list(input_list, urls):
    return [item for item in input_list if not any(url in item[0] for url in urls)]

a.datas = remove_from_list(a.datas, [
    'matplotlib', 'qt5', 'tk', 'tcl', 'PyQt5'
])

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mindpilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(current_dir, 'icon.ico') if os.path.exists(os.path.join(current_dir, 'icon.ico')) else None,
)