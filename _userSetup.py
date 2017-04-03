#maya�I������SiShelf�̏�Ԃ��L�^
import SiShelf.shelf
SiShelf.shelf.make_quit_app_job()
#UI�\�z���SiShelf�𕜌�
import maya.utils
maya.utils.executeDeferred(SiShelf.shelf.restoration_docking_ui)
