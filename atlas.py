import os
import nrrd
import numpy as np
from allensdk.api.queries.mouse_connectivity_api import MouseConnectivityApi
from allensdk.config.manifest import Manifest
from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.core.structure_tree import StructureTree
from allensdk.core.reference_space import ReferenceSpace

voxel_res = {10:(1320, 800, 1140), 25:(528, 320, 456), 50:(264, 160, 228), 100:(132, 80, 114)}
axes = ['AP', 'DV', 'ML']
um_range = dict(zip(axes, np.multiply(voxel_res[10], 10)))

class atlas():
    def __init__(self, res=25, sub=100):
        if res not in voxel_res.keys():
            raise Exception('Invalid resolution for annotation.')
        if sub not in voxel_res.keys():
            raise Exception('Invalid subsampling resolution.')
            
        self.voxel_res = dict(zip(axes, voxel_res[res]))
        self.sub_res = dict(zip(axes, voxel_res[sub]))
            
        oapi = OntologiesApi()
        structure_graph = oapi.get_structures_with_sets([1])
        structure_graph = StructureTree.clean_structures(structure_graph)
        self.tree = StructureTree(structure_graph)

        annotation_dir = 'annotation'
        Manifest.safe_mkdir(annotation_dir)
        annotation_path = os.path.join(annotation_dir, MouseConnectivityApi.CCF_VERSION_DEFAULT + '_' + str(res) + '.nrrd')

        if not os.path.exists(annotation_path):
            annotation_version = MouseConnectivityApi.CCF_VERSION_DEFAULT
            mcapi = MouseConnectivityApi()
            mcapi.download_annotation_volume(annotation_version, res, annotation_path)

        self.annotation, meta = nrrd.read(annotation_path)
        
        self.rsp = ReferenceSpace(self.tree, self.annotation, [res, res, res])
        self.down_rsp = self.rsp.downsample((sub, sub, sub))

    def get_sections(self, coor, sub=False):
        if sub:
            coronal = self.down_rsp.get_slice_image(0, coor["AP"])
            horizontal = self.down_rsp.get_slice_image(1, coor["DV"])
            sagittal = self.down_rsp.get_slice_image(2, coor["ML"])
        else:
            coronal = self.rsp.get_slice_image(0, coor["AP"])
            horizontal = self.rsp.get_slice_image(1, coor["DV"])
            sagittal = self.rsp.get_slice_image(2, coor["ML"])
        
        return coronal, horizontal.transpose([1, 0, 2]), sagittal.transpose([1, 0, 2])
    
    def px2um(self, ax, val, sub=False):
        if sub:
            return val / self.sub_res[ax] * um_range[ax]
        else:
            return val / self.voxel_res[ax] * um_range[ax]
        
    def um2px(self, ax, val, sub=False):
        if sub:
            return val / um_range[ax] * self.sub_res[ax]
        else:
            return val / um_range[ax] * self.voxel_res[ax]


class structTree():
    def __init__(self, ids, names):
        levels = [len(x) for x in ids.values()]
        keys = list(ids.keys())
        
        if levels.count(1) == 1:
            self.root = _node(names[keys[levels.index(1)]], keys[levels.index(1)])
            [self.root.insert(names[k], k) for key_lvl, k in zip(levels, keys) if key_lvl == 2]
            shift = 1
        else:
            self.root = _node('root', -1)
            [self.root.insert(names[k], k) for key_lvl, k in zip(levels, keys) if key_lvl == 1]
            shift = 0
        for l in range(2, max(levels) + 1):
            lvl_nodes = self.list_nodes(l)
            for k in [k for key_lvl, k in zip(levels, keys) if key_lvl == l+shift]:
                [n.insert(names[k], k) for n in lvl_nodes if n.val in ids[k]]
        
    def list_nodes(self, lvl, node=None): #list nodes at tree level
        if not lvl:
            return list()
        if not node:
            children = self.root.children
        else:
            children = node.children
        nodes = list()
        for c in children:
            nodes += self.list_nodes(lvl-1, c)
        if nodes:
            return nodes
        else:
            return children
        

class _node():
    def __init__(self, name, val, parent=None):
        self.name = name
        self.val = val
        self.parent = parent
        self.children = list()
    
    def insert(self, name, val):
        self.children.append(_node(name, val, parent=self))