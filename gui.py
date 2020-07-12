import sys
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
#from matplotlib.figure import Figure
import numpy as np
from atlas import atlas, structTree
import atlas as at

pane_axes = {0: ['ML', 'DV'],
             1: ['AP', 'DV'],
             2: ['AP', 'ML']}

default_coor = {"AP": 800, "DV": 800, "ML": 800}

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        fig, self.axs = plt.subplots(2, 2, sharex='col', sharey='row', gridspec_kw={'hspace': 0, 'wspace': 0})
        self.axs[1, 0].remove()
        self.axs = self.axs.flatten()
        self.axs = np.delete(self.axs, 2)
        super(MplCanvas, self).__init__(fig)
        plt.close(fig)
        
        
class CoorWidget(QtWidgets.QWidget):
    def __init__(self, lims, parent=None):
        super(CoorWidget, self).__init__()
        self.parent = parent
        self.labels = [QtWidgets.QLabel(parent=self, text=t) for t in at.axes]
        self.text = [QtWidgets.QLineEdit(self) for t in at.axes]
        
        layout = QtWidgets.QHBoxLayout()
        layout.addStretch()
        for l, t in zip(self.labels, self.text):
            t.setMaxLength(8)
            t.setFixedWidth(100)
            t.editingFinished.connect(self.on_edit)
            validator = QtGui.QDoubleValidator(bottom=0, top=lims[l.text()])
            t.setValidator(validator)
            layout.addWidget(l)
            layout.addWidget(t)
        layout.addStretch()
        self.setLayout(layout)
        
    def on_edit(self):
        coor = default_coor
        for l, t in zip(self.labels, self.text):
            coor[l.text()] = float(t.text())
        self.parent.update_coor(coor)
        
    def set_coor(self, coor):
        for l, t in zip(self.labels, self.text):
            t.setText(str(round(coor[l.text()], 2)))
        
        
class TreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, atlas, parent=None):
        id_tree = atlas.tree.get_ancestor_id_map()
        id_names = atlas.tree.get_name_map()
        tree = structTree(id_tree, id_names)
        super(TreeWidget, self).__init__()
        self.crawl_tree(self, tree.root)
        self.list = list()
        self.itemChanged.connect(self.on_change)
        self.topLevelItem(0).setExpanded(True)
        
    def crawl_tree(self, qtnode, node):
        item = QtWidgets.QTreeWidgetItem(qtnode, [node.name, str(node.val)])
        item.setCheckState(0, QtCore.Qt.Unchecked)
        item.setChildIndicatorPolicy(QtWidgets.QTreeWidgetItem.DontShowIndicatorWhenChildless)
        for c in node.children:
            self.crawl_tree(item, c)
            
    def on_change(self, item):
        if item.checkState(0) == QtCore.Qt.Checked:
            self.list.append(item.text(0))
            self._uncheck_parents(item)
            self._uncheck_children(item)
        else:
            self.list.remove(item.text(0))
        print(self.list)
        
    def _uncheck_children(self, item):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, QtCore.Qt.Unchecked)
            self._uncheck_children(child)
            
    def _uncheck_parents(self, item):
        parent = item.parent()
        if not parent:
            return
        parent.setCheckState(0, QtCore.Qt.Unchecked)
        self._uncheck_parents(parent)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        print('Initializing atlas...')
        self.at = atlas()
        self.coor = default_coor
        
        print('Initializing canvas...')
        self.sc = MplCanvas(self)
        
        self.crosshair = np.array([[i.axvline(0) for i in self.sc.axs], [i.axhline(0) for i in self.sc.axs]])
        self.sc.mpl_connect('button_press_event', self.on_click)
        
        print('Building structures tree...')
        self.treeWidget = TreeWidget(self.at)
        self.treeDockWidget = QtWidgets.QDockWidget()
        self.treeDockWidget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.treeDockWidget.setWidget(self.treeWidget)
        
        print('Initializing coordinates widget...')
        self.coorWidget = CoorWidget(at.um_range, parent=self)
        self.coorDockWidget = QtWidgets.QDockWidget()
        self.coorDockWidget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        self.coorDockWidget.setWidget(self.coorWidget)
    
        self.setCentralWidget(self.sc)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.treeDockWidget)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.coorDockWidget)
        
        self._make_menu()
        self.update_coor()
        self.show()
        
    def _make_menu(self):
        self.menu = self.menuBar()
        self.mfile = self.menu.addMenu('File')
        export = QtWidgets.QAction('Save Image', self)
        export.setShortcut(QtGui.QKeySequence.Save)
        self.mfile.addAction(export)
        settings = QtWidgets.QAction('Settings', self)
        self.mfile.addAction(settings)
        quit = QtWidgets.QAction('Quit', self)
        quit.setShortcut(QtGui.QKeySequence.Quit)
        self.mfile.addAction(quit)
        
        self.mview = self.menu.addMenu('View')
        viewgroup = QtWidgets.QActionGroup(self.mview)
        slice = QtWidgets.QAction('Slice View', self.mview, checkable=True)
        slice.setShortcut(QtGui.QKeySequence(self.tr("Ctrl+1")))
        eagle = QtWidgets.QAction('Eagle View', self.mview, checkable=True)
        eagle.setShortcut(QtGui.QKeySequence(self.tr("Ctrl+2")))
        viewgroup.addAction(slice)
        viewgroup.addAction(eagle)
        viewgroup.setExclusive(True)
        self.mview.addAction(slice)
        self.mview.addAction(eagle)
        slice.setChecked(True)
        
        self.mtool = self.menu.addMenu('Tools')
        
    def on_click(self, event):
        ax = event.inaxes
        idx = idx = [i for i, t in enumerate(self.sc.axs) if ax is t]
        if not idx:
            return
        idx = idx[0]
        self.coor[pane_axes[idx][0]] = self.at.px2um(pane_axes[idx][0], event.xdata, sub=True)
        self.coor[pane_axes[idx][1]] = self.at.px2um(pane_axes[idx][1], event.ydata, sub=True)
        self.update_coor()
        print('New coordinate: ', self.coor)
        
    def update_coor(self, coor=None):
        if coor:
            self.coor = coor
        self.draw_panes()
        self.update_crosshair()
        self.coorWidget.set_coor(self.coor)
        
    def update_crosshair(self):
        for i in np.arange(self.sc.axs.size):
            self.crosshair[0, i].set_xdata(self.at.um2px(pane_axes[i][0], self.coor[pane_axes[i][0]], True))
            self.crosshair[1, i].set_ydata(self.at.um2px(pane_axes[i][1], self.coor[pane_axes[i][1]], True))
        self.sc.draw()
        
    def draw_panes(self):
        coronal, horizontal, sagittal = self.at.get_sections(self.coor, True)
        self.sc.axs[0].imshow(coronal, interpolation='none', aspect='auto')
        self.sc.axs[1].imshow(sagittal, interpolation='none', aspect='auto')
        self.sc.axs[2].imshow(horizontal, interpolation='none', aspect='auto')
        self.sc.draw()


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()
