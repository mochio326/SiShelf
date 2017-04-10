# # -*- coding: utf-8 -*-

import maya.cmds as cmds


def __register_sishelf_startup():
    from textwrap import dedent
    cmds.evalDeferred(dedent(
        """
        import SiShelf.startup as s

        s.execute()
        """
    ))


if __name__ == '__main__':
    try:
        print("SiShelf startup script has begun")
        __register_sishelf_startup()
        print("SiShelf startup script has finished")

    except Exception as e:
        print("SiShelf startup script has ended with error")
        # avoidng the "call userSetup.py chain" accidentally stop,
        # all exception must be collapsed
        import traceback
        traceback.print_exc()
