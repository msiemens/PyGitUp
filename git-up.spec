# -*- mode: python -*-
a = Analysis(['PyGitUp\\gitup.py'],
             pathex=['F:\\Dokumente\\Coding\\python\\PyGitUp'],
             hiddenimports=['urllib2', 'bisect'],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='git-up.exe',
          debug=False,
          strip=None,
          upx=True,
          console=True )
