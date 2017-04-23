# -*- coding: utf-8 -*-
from textwrap import dedent
import maya.cmds as cmds
import maya.mel as mel
import maya.utils
from . import shelf
from . import lib

def menu_setup():
    cmd = '''
    buildViewMenu MayaWindow|mainWindowMenu;
    setParent -menu "MayaWindow|mainWindowMenu";
    '''

    mel.eval(cmd)

    cmds.menuItem(divider=True)
    cmds.menuItem(
        'sishelf_folder',
        label='SiShelf',
        subMenu=True,
        tearOff=True
    )

    cmds.menuItem(
        'sishelf_open',
        label=jpn('SiShelf'),
        annotation="open SiShelf",
        parent='sishelf_folder',
        echoCommand=True,
        command=dedent(
            '''
                import sishelf.shelf
                sishelf.shelf.main()
            ''')
    )

    cmds.menuItem(
        'sishelf_open_on_mouse',
        label=jpn('SiShelf on mouse'),
        annotation="open SiShelf on mouse",
        parent='sishelf_folder',
        echoCommand=True,
        command=dedent(
            '''
                import sishelf.shelf
                sishelf.shelf.popup()
            ''')
    )

    cmds.menuItem(
        'sishelf_xpop',
        label=jpn('SiShelf XPOP'),
        annotation="open SiShelf XPOP",
        parent='sishelf_folder',
        echoCommand=True,
        command=dedent(
            '''
                import sishelf.xpop
                sishelf.xpop.main()
            ''')
    )

def register_runtime_command(opt):

    # check if command already exists, then skip register
    runtime_cmd = dedent('''
        runTimeCommand
            -annotation "{annotation}"
            -category "{category}"
            -commandLanguage "{commandLanguage}"
            -command ({command})
            {cmd_name};
    ''')

    name_cmd = dedent('''
        nameCommand
            -annotation "{annotation}"
            -sourceType "{commandLanguage}"
            -command ("{cmd_name}")
            {cmd_name}NameCommand;
    ''')

    exits = mel.eval('''exists "{}";'''.format(opt['cmd_name']))
    if exits:
        return

    try:
        mel.eval(runtime_cmd.format(**opt))
        mel.eval(name_cmd.format(**opt))

    except Exception as e:
        print opt['cmd_name']
        print opt['command']
        raise e


def register_sishelf_runtime_command():
    opts = {
        'annotation':      "Open SiShelf",
        'category':        "SiShelf",
        'commandLanguage': "python",
        'command':         r'''"import sishelf.shelf as ss\r\nss.main() "''',
        'cmd_name':        "OpenSiShelf"
    }
    register_runtime_command(opts)

    opts = {
        'annotation':      "Open SiShelf on mouse position",
        'category':        "SiShelf",
        'commandLanguage': "python",
        'command':         r'''"import sishelf.shelf as ss\r\nss.popup() "''',
        'cmd_name':        "OpenSiShelfOnMouse"
    }
    register_runtime_command(opts)

    opts = {
        'annotation':      "SiShelf XPOP",
        'category':        "SiShelf",
        'commandLanguage': "python",
        'command':         r'''"import sishelf.xpop as xp\r\nxp.main() "''',
        'cmd_name':        "SiShelfXPOP"
    }
    register_runtime_command(opts)

def register_events():
    # Maya Save shelf state on exit
    shelf.make_quit_app_job()


def restore_shelf():
    # Restore docking state at startup
    maya.utils.executeDeferred(shelf.restoration_docking_ui)


def jpn(string):
    # type: (str) -> str
    """encode utf8 into cp932"""

    try:
        string = unicode(string, "utf-8")
        string = string.encode("cp932")
        return string

    except Exception:
        return string


def execute():
    menu_setup()
    register_sishelf_runtime_command()
    # 2017以降ではworkspaceControlがあるので記録と復元は必要ない
    if lib.maya_api_version() < 201700:
        register_events()
        restore_shelf()