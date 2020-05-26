## -*- coding: utf-8 -*-
import maya.cmds as cmds

def node_select(selectpartslist):
    newselectpartslist = []
    for i in selectpartslist:
        if cmds.objExists(i):
            newselectpartslist.append(i)
        else:
            print 'No Object "'+i+'" !!!'
    modi = cmds.getModifiers()
    if modi == 0:
        cmds.select(newselectpartslist, r=True)
    elif modi == 1:
        cmds.select(newselectpartslist, tgl=True)
    elif modi == 5:
        cmds.select(newselectpartslist, add=True)
    elif modi == 4:
        cmds.select(newselectpartslist, d=True)
    #cmds.setFocus("MayaWindow")
