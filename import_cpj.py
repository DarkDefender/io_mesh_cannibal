# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------------------------
import colorsys
import bpy
import bmesh

import os, sys

# Add the current directory to the search path so our local imports will work
sys.path.append(os.path.dirname(__file__))

from cpj_utils import *
from formats.geo import Geo
from formats.srf import Srf
from formats.mac import Mac

# ----------------------------------------------------------------------------
def load(context, filepath):

    # info
    print("Reading %s..." % filepath)

    cpj_data = load_cpj_data(filepath)

    # Load in all geometry data
    # TODO load in more that one GEO entry if there are any
    geo_data = Geo.from_bytes(cpj_data["GEOB"][0])

    bl_object = load_geo(geo_data)

    # Load in all surface data
    # TODO load in more that one SRF entry if there are any
    srf_data = Srf.from_bytes(cpj_data["SRFB"][0])

    load_srf(srf_data, bl_object)

    # Load Model Actor Configuation data
    mac_data = Mac.from_bytes(cpj_data["MACB"][0])

    load_mac(mac_data)

    return {'FINISHED'}

# Load mesh geometry data into Blender.
def load_geo(geo_data):
    # TODO this currently only load the basic triangle mesh
    # This doesn't respect any other data from the geometry data structure currently.

    verts = geo_data.data_block.vertices
    vert_len = len(verts)

    cpj_verts = []

    for vert in verts:
        ref = vert.ref_pos
        cpj_verts.append((ref.x, ref.z, ref.y))

    edges = geo_data.data_block.edges

    #for edge in edges:

    tris = geo_data.data_block.triangles

    # Create a list of mesh faces
    bl_faces = []
    for tri in tris:
        e0 = tri.edge_ring[0]
        e1 = tri.edge_ring[1]
        e2 = tri.edge_ring[2]

        v0 = edges[e0].tail_vertex
        v1 = edges[e1].tail_vertex
        v2 = edges[e2].tail_vertex
        bl_faces.append((v0, v1, v2))

    name = "No_name_defined"

    if hasattr(geo_data, 'name'):
        name = geo_data.name

    mesh_data = bpy.data.meshes.new(name)
    mesh_data.from_pydata(cpj_verts, [], bl_faces)
    mesh_data.update()
    obj = bpy.data.objects.new(name, mesh_data)
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    return obj

# Load mesh texture and UV data into Blender.
def load_srf(srf_data, bl_object):
    # Create new empty UV layer
    bl_uv_layer = bl_object.data.uv_layers.new(name="cpj_uv", do_init=False)

    # Init BMesh with our existing object mesh
    bm = bmesh.new()
    bm.from_mesh(bl_object.data)
    bm.faces.ensure_lookup_table()
    uv = bm.loops.layers.uv[0]

    # Sanity check
    if srf_data.num_tris != len(bm.faces):
        raise ImportError("Different number of mesh faces in GEO and SRF")

    textures = srf_data.data_block.textures

    h_val = 0.0

    # Create materials
    for tex in textures:
        # Make new texture with incremental colors
        col = colorsys.hls_to_rgb(h_val % 1.0, 0.6, 0.8)
        mat = bpy.data.materials.new(name=tex.name)
        mat.diffuse_color = (col[0], col[1], col[2], 1.0)
        bl_object.data.materials.append(mat)
        # TODO use tex.ref_name to look up the image texture
        h_val += 0.1

    tris = srf_data.data_block.tris
    uvs = srf_data.data_block.uvs

    # Create the UV map
    for i in range(len(tris)):
        tri = tris[i]

        uv0_idx = tri.uv_index[0]
        uv1_idx = tri.uv_index[1]
        uv2_idx = tri.uv_index[2]

        uv0 = (uvs[uv0_idx].u, 1.0 - uvs[uv0_idx].v)
        uv1 = (uvs[uv1_idx].u, 1.0 - uvs[uv1_idx].v)
        uv2 = (uvs[uv2_idx].u, 1.0 - uvs[uv2_idx].v)

        bm.faces[i].loops[0][uv].uv = uv0
        bm.faces[i].loops[1][uv].uv = uv1
        bm.faces[i].loops[2][uv].uv = uv2

        # set material index
        bm.faces[i].material_index = tri.tex_index

    # TODO handle the flags, smoothing groups, alpha level, and glaze data stored in the triangle srf data.

    # Update our object mesh
    bm.to_mesh(bl_object.data)
    bm.free()

def load_mac(mac_data):
    # TODO handle sections
    # mac_data.data_block.sections[0]

    # TODO actually act on the data stored here so we set the origin and scale of the object etc etc...

    mac_text = bpy.data.texts.new("cbj_" + mac_data.name)

    for com in mac_data.data_block.commands:
        mac_text.write(com.command_str + "\n")

