# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get current directory
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
hiddenimports.extend(['sqlite3'])

# 收集数据文件
datas = []
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

a = Analysis(
    [os.path.join(src_dir, 'main.py')],  # 使用绝对路径
    pathex=[src_dir],  # 添加源码目录到Python路径
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mindpilot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mindpilot',
)