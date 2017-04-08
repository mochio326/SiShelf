# Maya Save shelf state on exit
import SiShelf.shelf
SiShelf.shelf.make_quit_app_job()
# Restore docking state at startup
import maya.utils
maya.utils.executeDeferred(SiShelf.shelf.restoration_docking_ui)
