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

from cpj_utils import *

from formats.frm import Frm
from formats.geo import Geo
from formats.srf import Srf
from formats.skl import Skl
from formats.mac import Mac

# ----------------------------------------------------------------------------
def load(context, filepath):

    # info
    print("Reading %s..." % filepath)

    cpj_data = load_cpj_data(filepath)

    if len(cpj_data["GEOB"]) > 1:
        raise Exception('Importing cpjs with more than one mesh in it is not supported yet')
        return {'CANCELLED'}

    # Load in all geometry data
    # TODO load in more than one GEO entry if there are any
    geo_data = Geo.from_bytes(cpj_data["GEOB"][0])

    obj = load_geo(geo_data)

    if len(cpj_data["SRFB"]) > 1:
        raise Exception('Importing cpjs with more than one surface in it is not supported yet')
        return {'CANCELLED'}

    # Load in all surface data
    # TODO load in more than one SRF entry if there are any
    srf_data = Srf.from_bytes(cpj_data["SRFB"][0])

    load_srf(srf_data, obj.data)

    # Load vertex animation data as shape keys
    # TODO load in more than one FRM entry if there are any
    frm_data = Frm.from_bytes(cpj_data["FRMB"][0])

    load_frm(frm_data, obj)

    # Load in all surface data
    # TODO load in more that one SKL entry if there are any
    # And the rest of it lol
    skl_data = Skl.from_bytes(cpj_data["SKLB"][0])

    load_skl(skl_data, bl_object)

    # Load Model Actor Configuation data
    mac_data = Mac.from_bytes(cpj_data["MACB"][0])

    load_mac(mac_data)

    return {'FINISHED'}

def load_frm(frm_data, obj):
    verts = obj.data.vertices

    # TODO import all frames and update this function to support this
    sk_basis = obj.shape_key_add(name='Basis')
    sk_basis.interpolation = 'KEY_LINEAR'
    obj.data.shape_keys.use_relative = False

    for frame in frm_data.data_block.frames:
        # Create new shape key
        sk = obj.shape_key_add(name=frame.name)
        sk.interpolation = 'KEY_LINEAR'

        uses_group_compression = (frame.num_groups != 0)

        pos = [0.0]*3

        for i, vert in enumerate(frame.verts):
            if uses_group_compression:
                group_data = frame.groups[vert.group]
                byte_pos = vert.pos
                byte_pos[0] *= group_data.byte_scale.x
                byte_pos[1] *= group_data.byte_scale.y
                byte_pos[2] *= group_data.byte_scale.z

                byte_pos[0] += group_data.byte_translate.x
                byte_pos[1] += group_data.byte_translate.y
                byte_pos[2] += group_data.byte_translate.z

                pos = byte_pos
            else:
                pos = vert.pos

            # position each vert
            sk.data[i].co.x = pos[0]
            sk.data[i].co.y = -pos[2]
            sk.data[i].co.z = pos[1]


def create_custom_data_layers(mesh_data):
    # NOTE: We are not using the return values from the .new functions as there
    # currently a bug/quirk in Blender that makes them invalid if the attribute
    # layer array is re-allocated when adding new layers

    # Create custom data layer for vertices
    # They only have one flag (LODLOCK) so this is essentially a boolean
    mesh_data.attributes.new("lod_lock", 'INT', 'POINT')
    # This seems to be used to setup vertex data compression for vertex animations (FRM)
    mesh_data.attributes.new("frm_group_index", 'INT', 'POINT')

    # Create custom data layers for the triangles
    mesh_data.attributes.new("flags", 'INT', 'FACE')
    mesh_data.attributes.new("smooth_group", 'INT', 'FACE')
    mesh_data.attributes.new("alpha_level", 'INT', 'FACE')
    mesh_data.attributes.new("glaze_index", 'INT', 'FACE')
    # The glaze func only have one enum value so this is actually just a boolean
    mesh_data.attributes.new("glaze_func", 'INT', 'FACE')

# Load mesh geometry data into Blender.
def load_geo(geo_data):
    verts = geo_data.data_block.vertices
    vert_len = len(verts)

    cpj_verts = []

    for vert in verts:
        ref = vert.ref_pos
        # Convert the vertex position into the correct transformation space for Blender
        cpj_verts.append((ref.x, -ref.z, ref.y))

    edges = geo_data.data_block.edges

    #for edge in edges:

    tris = geo_data.data_block.triangles

    # Create a list of mesh faces
    bl_faces = []
    for tri in tris:

        # Do the reverse winding of the triangle here as otherwise the triangles will
        # become inverted because we convert the vertex coordinates to the Blender
        # coordinate system.
        e0 = tri.edge_ring[2]
        e1 = tri.edge_ring[1]
        e2 = tri.edge_ring[0]

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

    create_custom_data_layers(mesh_data)

    lod_lock_layer = mesh_data.attributes["lod_lock"]
    group_index_layer = mesh_data.attributes["frm_group_index"]

    for i, vert in enumerate(verts):
        # As 'flags' can only be 0 or 1, we don't need to do any type casting
        lod_lock_layer.data[i].value = vert.flags
        group_index_layer.data[i].value = vert.group_index

    # TODO load mount points with empties

    return obj

# Load mesh texture and UV data into Blender.
def load_srf(srf_data, mesh_data):
    # Create new empty UV layer
    bl_uv_layer = mesh_data.uv_layers.new(name=srf_data.name, do_init=False)

    # Init BMesh with our existing object mesh
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.faces.ensure_lookup_table()
    uv_layer = bm.loops.layers.uv[0]

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
        mesh_data.materials.append(mat)
        if tex.ref_name:
            # TODO use tex.ref_name to look up the image texture
            mat["CPJ texture ref"] = tex.ref_name
        h_val += 0.1

    tris = srf_data.data_block.tris
    uvs = srf_data.data_block.uvs

    # Create the UV map
    for i, tri in enumerate(tris):
        # This is reversing the loop because we reversed the vertex loop order for the geometry itself as well
        uv0_idx = tri.uv_index[2]
        uv1_idx = tri.uv_index[1]
        uv2_idx = tri.uv_index[0]

        uv0 = (uvs[uv0_idx].u, 1.0 - uvs[uv0_idx].v)
        uv1 = (uvs[uv1_idx].u, 1.0 - uvs[uv1_idx].v)
        uv2 = (uvs[uv2_idx].u, 1.0 - uvs[uv2_idx].v)

        bm.faces[i].loops[0][uv_layer].uv = uv0
        bm.faces[i].loops[1][uv_layer].uv = uv1
        bm.faces[i].loops[2][uv_layer].uv = uv2

        # set material index
        bm.faces[i].material_index = tri.tex_index

    # Update our object mesh
    bm.to_mesh(mesh_data)
    bm.free()



    flags_layer = mesh_data.attributes["flags"]
    smooth_group_layer = mesh_data.attributes["smooth_group"]
    alpha_level_layer = mesh_data.attributes["alpha_level"]
    glaze_index_layer = mesh_data.attributes["glaze_index"]
    glaze_func_layer = mesh_data.attributes["glaze_func"]

    for i, tri in enumerate(tris):
        flags_layer.data[i].value = tri.flags
        smooth_group_layer.data[i].value = tri.smooth_group
        alpha_level_layer.data[i].value = tri.alpha_level
        glaze_index_layer.data[i].value = tri.glaze_tex_index
        glaze_func_layer.data[i].value = tri.glaze_func

# Load skeleton bones as blender armatures


def load_skl(skl_data, bl_object):
    # Data has location of bones
    # Zeddb (wisely) advises two passes:
    # Pass 1: create bones and set their parents
    # Pass 2: transform the bones
    # This is because  bones in cpj data have parent-sensitive transforms.

    # bl_object and ob_armature might refer to the same thing.
    # If they do, prefer bl_object

    # skl.yaml is the KaiTai parser source
    indexToBoneName = {}

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    ob_armature = bpy.context.active_object  # Should I use bl_object?
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

        # apply vertex and weight?
        # potentially yes. Vertex/ Vertex Groups are
        # shared between data in cpj. Or, rather, Vertex[i] in the
        # geo is Vertex[i] in the skl. So, if the geo already has
        # vertex groups...

    # Pass 2: Set bone parents
    for bone_index in range(len(bone_datas)):
        if bone_index != -1:  # -1 is root bone/no parent
            bone_data = bone_datas[bone_index]
            bone = created_bones[bone_index]
            bone.parent = edit_bones[bone_data.parent_name]

    # Pass 3: Transform bones
    for bone_index in range(len(bone_datas)):
        pose_bone = ob_armature.pose.bones[bone_index]
        bone_data = bone_datas[bone_index]

        # might need to change head and tail locations first
        # If we assume that a bone's origin is its center,
        # then the head and tail would be location +/- length/2
        # in the direction of the rotation.

        bone_trans = bone_data.base_translate
        pose_bone.location = [bone_trans.x, -bone_trans.z, bone_trans.y]

        # Recreating quat in a way blender recognizes
        pose_bone.rotation_quaternion = bpy.MathUtils.Quaternion(
            bone_data.base_rotate.s,
            bone_data.base_rotate.v.x,
            bone_data.base_rotate.v.y,
            bone_data.base_rotate.v.z
        )

        pose_bone.scale = bone_data.base_scale

    # Pass 4: Apply Vertex Groups and Weights
    # This loop gets to be n^2 because it does 2 things
    weight_shift = 0
    vertex_data = skl_data.data_block.verts
    weight_data = skl_data.data_block.weights
    for vert_index in range(len(ob_armature.verticies)):
        vertex = ob_armature.verticies[vert_index]
        weight_range = range(
            vert_index + weight_shift,
            vert_index + weight_shift + vertex_data[vert_index].num_weights)
        for local_weight_index in weight_range:
            group_index = local_weight_index - vert_index - weight_shift
            # add group to vertex.groups
            # index is the relative index of the weight
            # groups might already exist? unsure, double-check importer
            vertex.groups[group_index] = bpy.context.active_object.vertex_groups.new(
                name=f'{vert_index}-{group_index}')

            # set group weight to be weight_data[local_weight_index].weight_factor
            vertex.groups[group_index].weight = weight_data[local_weight_index].weight_factor

            # somehow? add bone at
            #   edit_bones[weight_data[local_weight_index].bone_index] to the
            #   vertex/group
            # wait... is that even a thing? I'm not sure...
            # And something might happen with weight_data[local_weight_index].offset_pos

    # Finally, set current pose as rest pose
    bpy.ops.pose.armature_apply(selected=False)

    # Then potentially add verticies, weights, and mount points.

def load_mac(mac_data):
    # TODO mac data loading correctly

    mac_text = bpy.data.texts.new("cpj_" + mac_data.name)
    for sec in mac_data.data_block.sections:
        # Write section name start delimiter
        mac_text.write("--- " + sec.name + "\n")

        # TODO actually act on the data stored here so we set the origin and scale of the object etc etc...
        # ONLY if the command section is "autoexec" though!!!
        # The other sections we don't know what to do with. But they should be kept intact as per the format spec
        start_com = sec.first_command
        end_com = start_com + sec.num_commands
        for com in mac_data.data_block.commands[start_com:end_com]:
            mac_text.write(com.command_str + "\n")

