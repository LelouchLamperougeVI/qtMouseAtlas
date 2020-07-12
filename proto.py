import sys
from atlas import atlas, structTree
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
from PyQt5 import QtCore, QtGui, QtWidgets

at = atlas()

id_tree = at.tree.get_ancestor_id_map()
id_names = at.tree.get_name_map()

my_tree = structTree(id_tree, id_names)

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QWidget()
layout = QtWidgets.QVBoxLayout(window)

def crawl_tree(qtnode, node):
    item = QtWidgets.QTreeWidgetItem(qtnode, [node.name, str(node.val)])
    item.setCheckState(0, QtCore.Qt.Unchecked)
    item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicatorWhenChildless)
    for c in node.children:
        crawl_tree(item, c)
 
root = QtWidgets.QTreeWidget()
crawl_tree(root, my_tree.root)

layout.addWidget(root)
window.show()
app.exec_()