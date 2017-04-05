#maya終了時にシェルフの状態を保存
import SiShelf.shelf
SiShelf.shelf.make_quit_app_job()
#ドッキング状態を起動時に復元
import maya.utils
maya.utils.executeDeferred(SiShelf.shelf.restoration_docking_ui)
