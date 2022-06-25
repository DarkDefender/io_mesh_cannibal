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
from formats.skl import Skl
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

    # Load in all surface data
    # TODO load in more that one SKL entry if there are any
    # And the rest of it lol
    skl_data = Skl.from_bytes(cpj_data["SKLB"][0])

    load_skl(skl_data, bl_object)

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
        cpj_verts.append((ref.x, -ref.z, ref.y))

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

# Load skeleton bones as blender armatures
def load_skl(skl_data, bl_object):
    # Data has location of bones
    # Zeddb (wisely) advises two passes:
    # Pass 1: create bones and set their parents
    # Pass 2: transform the bones
    # This is because  bones in cpj data have parent-sensitive transforms.

    # skl.yaml is the KaiTai parser source
    indexToBoneName = {}

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    ob_armature = bpy.context.active_object # Should I use bl_object?
    edit_bones = ob_armature.data.edit_bones

    # This entire scheme assumes the indexes in createdBones,
    # obArmature.pose.bones, and boneData.parent_index all point
    # to the same bone. Which they should. Yeah.

    created_bones = []
    bone_datas = skl_data.data_block.bones

    # Pass 1: Create bones
    for bone_data in bone_datas:
        working_bone = edit_bones.new(bone_data.name)
        working_bone.head = (0, 1, 2)   # do these head and tail
        working_bone.tail = (1, 2, 3)   # values matter? Like, does
                                        # Location in bose change them?
        created_bones.append(working_bone)

    # Pass 2: Set bone parents 
    for bone_index in range(len(bone_datas)):
        bone_data = bone_datas[bone_index]
        bone = created_bones[bone_index]
        bone.parent = edit_bones[bone_data.parent_name]

    # Pass 3: Transform bones
    for bone_index in range(len(bone_datas)):
        pose_bone = ob_armature.pose.bones[bone_index]
        bone_data = bone_datas[bone_index]

        # might need to change head and tail locations first
        # If we assume 
        
        bone_trans = bone_data.base_translate
        pose_bone.location = [bone_trans.x, bone_trans.z, bone_trans.y]

        # Is this legal?
        pose_bone.rotation_quaternion = bone_data.base_rotate

        pose_bone.scale = bone_data.base_scale

    # Finally, set current pose as rest pose
    bpy.ops.pose.armature_apply(selected=False)

    # Then potentially add verticies, weights, and mount points.


def load_mac(mac_data):
    # TODO handle sections
    # mac_data.data_block.sections[0]

    # TODO actually act on the data stored here so we set the origin and scale of the object etc etc...

    mac_text = bpy.data.texts.new("cbj_" + mac_data.name)

    for com in mac_data.data_block.commands:
        mac_text.write(com.command_str + "\n")

