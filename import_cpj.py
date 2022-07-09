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
import mathutils

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
    # Unlike other chunks, there has to be at least 1 GEO chunk
    geo_data = Geo.from_bytes(cpj_data["GEOB"][0])

    obj = load_geo(geo_data)

    if len(cpj_data["SRFB"]) > 1:
        raise Exception('Importing cpjs with more than one surface in it is not supported yet')
        return {'CANCELLED'}

    # Load in all surface data
    # TODO load in more than one SRF entry if there are any
    if "SRFB" in cpj_data:
        srf_data = Srf.from_bytes(cpj_data["SRFB"][0])

        load_srf(srf_data, obj.data)

    # Load vertex animation data as shape keys
    # TODO load in more than one FRM entry if there are any
    if "FRMB" in cpj_data:
        frm_data = Frm.from_bytes(cpj_data["FRMB"][0])

        load_frm(frm_data, obj)

    # Load in all skeleton data
    # TODO load in more that one SKL entry if there are any
    if "SKLB" in cpj_data:
        skl_data = Skl.from_bytes(cpj_data["SKLB"][0])

        load_skl(skl_data, obj)

    # Load Model Actor Configuation data
    # Unlike other chunks, there has to be at least 1 MAC chunk
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
    # Bones are handled in multiple passes since their
    # transforms are parent sensitive
    # skl.yaml is the KaiTai parser source

    # create armature first lol
    # bl_obj.new(name, armature id)
    # 
    # this is obj armature
    # then it needs to be a child of bl_object
    # first, create new armature data in bpy.data
    # then use bpy.data.objects.new(name, armature_data)
    # to create ob_armature
    # then make bl_object ob_armature's parent
    name = "No_name_defined"

    if hasattr(skl_data, 'name'):
        name = skl_data.name

    armature_data = bpy.data.armatures.new(name)
    ob_armature = bpy.data.objects.new(name, armature_data)
    
    scene = bpy.context.scene
    scene.collection.objects.link(ob_armature)
    ob_armature.parent = bl_object
    bpy.context.view_layer.objects.active = ob_armature
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = ob_armature.data.edit_bones

    #scene = bpy.context.scene
    #scene.collection.objects.link(obj)
    #

    # This entire scheme assumes the indexes in createdBones,
    # obArmature.pose.bones, and boneData.parent_index all point
    # to the same bone. Which they should. Yeah.

    #can probably get away with just using edit bones?
    created_bones = []
    bone_datas = skl_data.data_block.bones

    # Pass 1: Create bones
    for bone_data in bone_datas:

        working_bone = edit_bones.new(bone_data.name)
        # temp head and tail, these get set for real
        # once the parent is set
        working_bone.head = (0, 0, 0)
        working_bone.tail = (0, 0, bone_data.length)   

        #created_bones.append(working_bone)

    # Pass 2: Set bone parents
    for bone_index in range(len(bone_datas)):
        bone_data = bone_datas[bone_index]
        parent_index = bone_data.parent_index
        bone = edit_bones[bone_index]

        if parent_index >= 0:  # -1 is root bone/no parent
            bone.parent = edit_bones[parent_index]
            bone.use_connect = True

        # Now that parent is set, head/tail can be placed
        # uh... I think
        # Recreating quat in a way blender recognizes
        bone_quat = mathutils.Quaternion((
            bone_data.base_rotate.s,
            bone_data.base_rotate.v.x,
            bone_data.base_rotate.v.y,
            bone_data.base_rotate.v.z
        ))

        # There's probably a more succinct to express this math, but
        # I trust it's correct, so I'm doing it
        # This assumes that the rotate method maintains vector scale
        # and that bone.head/tail is compatable with Mathutils.Vector
        bhv = bone_data.base_translate
        bone_vec = mathutils.Vector((bhv.x, -bhv.z, bhv.y + bone_data.length))
        bone_vec.rotate(bone_quat)
        bone_vec = bone.head + bone_vec
        bone.tail = bone_vec

    # switch to pose mode, and probably also
    # add edit bones to the pose? or just make them
    # not be edit bones

    # TRANSFORM BONES BEFORE GOING TO POSE

    # So basically, use rot, scale, pos, and length of data
    # and center, head, and length of edit_bone to place the bone
    # correctly. Then apply them in the bose just to be safe

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bpy.ops.object.mode_set(mode='POSE', toggle=False)


    # Pass 2-and-a-half: Generate Bones because edit bones are fake
    # and made of lies, apparently?

    # Pass 3: Transform bones
    # There end up being more pose bones than bone datas,
    # somehow. Maybe because the root bone doesn't count?
    # idk add a qualifier to it so if it's out of range
    # on ob_armature.pose.bones it just continues
    for bone_index in range(len(bone_datas)):

        if not (bone_index in ob_armature.pose.bones.keys()):
            continue

        pose_bone = ob_armature.pose.bones[bone_index]
        bone_data = bone_datas[bone_index]

        bone_trans = bone_data.base_translate
        pose_bone.location = (bone_trans.x, -bone_trans.z, bone_trans.y)

        # Recreating quat in a way blender recognizes
        bone_quat = mathutils.Quaternion((
            bone_data.base_rotate.s,
            bone_data.base_rotate.v.x,
            bone_data.base_rotate.v.y,
            bone_data.base_rotate.v.z
        ))
        #pose_bone.rotation_quaternion = bone_quat

        bone_scl = bone_data.base_scale
        pose_bone.scale = (bone_scl.x, bone_scl.y, bone_scl.z)

    # Finally, set current pose as rest pose
    bpy.ops.pose.armature_apply(selected=False)
    return


    # Pass 4: Apply Vertex Groups and Weights
    # This loop gets to be n^2 because it does 2 things

    # Do we need to add verticies to the armature too?
    # Or can we just piggyback off of the geo's like I've been doing?
    # Documentation implies the first one...

    weight_shift = 0
    vertex_data = skl_data.data_block.verts
    weight_data = skl_data.data_block.weights
    
    for vert_index in range(len(bl_object.verticies)):
        vertex = bl_object.verticies[vert_index]
        vert_shift = vert_index + weight_shift

        for group_index in range(vertex_data[vert_index].num_weights):
            # add group to vertex.groups
            # index is the relative index of the weight
            vertex.groups[group_index] = bpy.context.active_object.vertex_groups.new(
                name=f'{vert_index}-{group_index}'
            )

            new_weight = weight_data[group_index + vert_shift].weight_factor
            vertex.groups[group_index].weight = new_weight

            # somehow? add bone at
            #   edit_bones[weight_data[local_weight_index].bone_index] to the
            #   vertex/group
            # wait... is that even a thing? I'm not sure...
            # And something might happen with weight_data[local_weight_index].offset_pos

    # Pass 5: Mount Points
    # but that can be later

    # Finally, set current pose as rest pose
    bpy.ops.pose.armature_apply(selected=False)


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

