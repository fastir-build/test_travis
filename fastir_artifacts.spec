# -*- mode: python -*-

import os.path
import sys


a = Analysis(['fastir_artifacts.py'],
             pathex=['.'],
             binaries=[],
             datas=[(os.path.join(sys.prefix, 'share', 'artifacts'), os.path.join('share', 'artifacts'))],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='fastir_artifacts',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          console=True,
          uac_admin=True,
          icon='favicon_sekoia_150x150_r6F_icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='fastir_artifacts')

if sys.platform == 'win32':
    import shutil
    # WOW64 redirection will pick up the right dll
    if (os.path.exists(os.path.join(os.environ['SYSTEMROOT'], 'System32', 'msvcp140.dll')) and
        not os.path.exists(os.path.join('dist', 'fastir_artifacts', 'msvcp140.dll'))):
        shutil.copy(os.path.join(os.environ['SYSTEMROOT'], 'System32', 'msvcp140.dll'), os.path.join('dist', 'fastir_artifacts'))
