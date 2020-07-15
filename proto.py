import sys
from atlas import atlas, structTree
import matplotlib.pyplot as plt
import numpy as np
import numba as nb
import matplotlib
from PyQt5 import QtCore, QtGui, QtWidgets
import time

at = atlas()

regions = ['Somatomotor areas', 'Frontal pole, cerebral cortex', 'Somatosensory areas', 
            'Gustatory areas', 'Visceral area', 'Auditory areas', 'Visual areas', 'Anterior cingulate area',
            'Retrosplenial area', 'Posterior parietal association areas']

# regions = ['root']

id_tree = at.tree.get_ancestor_id_map()
id_names = at.tree.get_name_map()
tree = structTree(id_tree, id_names)

nodes = tree.get_node_by_name(regions)

anno = at.annotation
colormap = at.tree.get_colormap()

@nb.njit(parallel=True, fastmath=True)
def fast_isin(a, b):
    init_shape = a.shape
    a = a.flatten()
    ret = np.empty(a.size, dtype=nb.boolean)
    b = set(b)
    
    for i in nb.prange(a.size):
        ret[i] = a[i] in b
    
    return ret.reshape(init_shape)
    
mask = np.zeros(anno.shape, int)
for n in nodes:
    lst = tree.list_descendent_ids(n)
    idx = fast_isin(anno, nb.typed.List(lst))
    mask[idx] = n.val
    
idx = np.expand_dims( np.argmax(mask>0, axis=1), axis=1)
projection = np.take_along_axis(mask, idx, axis=1).squeeze()

plt.imshow(projection)