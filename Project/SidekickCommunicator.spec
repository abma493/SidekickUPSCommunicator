# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('common', 'common'),
        ('screens', 'screens'),
    ],
    hiddenimports=[
        # pysnmp
        'pysnmp',
        'pysnmp.hlapi',
        'pysnmp.hlapi.v3arch',
        'pysnmp.hlapi.v3arch.asyncio',
        'pysnmp.smi',
        'pysnmp.smi.rfc1902',
        'pysnmp.smi.builder',
        'pysnmp.smi.view',
        'pysnmp.smi.compiler',
        'pysnmp.carrier',
        'pysnmp.carrier.asyncio',
        'pysnmp.carrier.asyncio.dgram',
        'pysnmp.carrier.asyncio.dgram.udp',
        'pysnmp.entity',
        'pysnmp.entity.engine',
        'pysnmp.entity.rfc3413',
        'pysnmp.entity.rfc3413.cmdgen',
        'pysnmp.entity.rfc3413.config',
        'pysnmp.proto',
        'pysnmp.proto.rfc1905',
        'pysnmp.proto.mpmod.rfc2576',
        'pysnmp.proto.mpmod.rfc3412',
        'pysnmp.proto.secmod.rfc2576',
        'pysnmp.proto.secmod.rfc3414',
        'pysnmp.proto.acmod.rfc3415',
        'pyasn1',
        'pyasn1.type.univ',
        'pyasn1.codec.ber',
        'pyasn1.codec.native',
        # pythonping
        'pythonping',
        # textual
        'textual',
        'textual.app',
        'textual.screen',
        'textual.widgets',
        'textual.containers',
        'textual.css',
        'textual.binding',
        # aiohttp
        'aiohttp',
        # asyncio
        'asyncio',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SidekickCommunicator',
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
    icon=r'C:\Users\ael493\OneDrive - University of Texas at San Antonio\Desktop\VertivComm\VertivCommunicator\Project\assets\sidekick_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SidekickCommunicator',
)
