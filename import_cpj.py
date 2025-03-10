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
from formats.seq import Seq
from formats.mac import Mac

import math
from math import pi

# ----------------------------------------------------------------------------
def get_loaded_data_name_safe(name, load_data_dict):
    if name in load_data_dict:
        # We loaded and names the object exactly as specified in the MAC file
        return name
    # Check if there are any partial "name.001" matches in case we have duplicates in the blend existing file.
    match = ""
    for key in load_data_dict:
        if key.startswith(name):
            match = key
    if match != "" and key[len(name)+1].isnumeric():
        return match

    print(load_data_dict.keys())
    raise ImportError("Couldn't load '" + name + "' as specified in the MAC data. No such data block was loaded into Blender")

def get_loaded_data_safe(name, load_data_dict):
    safe_name = get_loaded_data_name_safe(name, load_data_dict)
    return load_data_dict[safe_name]

def load(filepath, import_settings):

    # info
    print("Reading %s..." % filepath)

    cpj_data = load_cpj_data(filepath)

    if import_settings['only_import_animations']:
        # Load in all animaiton sequences
        if "SEQB" in cpj_data:
            obj = ""
            ob_armature = bpy.context.active_object

            if ob_armature.type != 'ARMATURE':
                raise ImportError("The active object needs to be an armature you want to import the animations to!")

            for seq_byte_data in cpj_data["SEQB"]:
                seq_data = Seq.from_bytes(seq_byte_data)

                load_seq(seq_data, obj, ob_armature, True)
        else:
            raise ImportError("This file doesn't containt any animation data. There are no SEQ chunks!")

        return {'FINISHED'}

    # Load Model Actor Configuation data
    # Unlike other chunks, there has to be at least 1 MAC chunk
    if len(cpj_data["MACB"]) == 0:
        raise ImportError("Doesn't seem to be a valid cpj file. There are no MAC chunks!")

    # Load in all geometry data
    geo_data_dict = {}
    for geo_byte_data in cpj_data["GEOB"]:
        geo_data = Geo.from_bytes(geo_byte_data)
        mesh_data, geo_mounts = load_geo(geo_data)
        geo_data_dict[mesh_data.name] = [mesh_data, geo_mounts]

    # Load in all LOD data
    # TODO

    # Load in all surface data
    srf_data_dict = {}
    if "SRFB" in cpj_data:
        for srf_byte_data in cpj_data["SRFB"]:
            srf_data = Srf.from_bytes(srf_byte_data)
            srf_data_dict[srf_data.name] = srf_data

    # Load in all skeleton data
    skl_data_dict = {}
    if "SKLB" in cpj_data:
        for skl_byte_data in cpj_data["SKLB"]:
            skl_data = Skl.from_bytes(skl_byte_data)
            arm_data = load_skl(skl_data)
            skl_data_dict[skl_data.name] = arm_data

    for mac_byte_data in cpj_data["MACB"]:
        mac_data = Mac.from_bytes(mac_byte_data)
        mac_commands = load_mac(mac_data)

        collection = bpy.data.collections.new(mac_data.name)
        bpy.context.scene.collection.children.link(collection)

        # Set Loc,Rot,Scale must be present
        loc = mac_commands["SetOrigin"]
        loc = -mathutils.Vector( (float(loc[0]), -float(loc[2]), float(loc[1])) )

        rot = mac_commands["SetRotation"]
        rot = [math.radians(float(rot[0])), math.radians(-float(rot[2])), math.radians(float(rot[1]))]

        scale = mac_commands["SetScale"]
        scale = [float(scale[0]), float(scale[2]), float(scale[1])]

        # There must be at least one geometry object
        if not "SetGeometry" in mac_commands:
            raise ImportError("Doesn't seem to be a valid cpj model file. There are no GEO chunks!")
        geo_name = mac_commands["SetGeometry"].strip('"')
        geo_name = get_loaded_data_name_safe(geo_name, geo_data_dict)
        geo_data = geo_data_dict[geo_name]

        # TODO This is to ensure that we can correctly import multiple objects using the same geo base mesh.
        # I guess this could be done in a cleaner way...
        geo_data_dict[geo_name] = [geo_data[0].copy(), geo_data[1]]

        obj = create_mesh_obj(mac_data.name, collection, geo_data)
        obj.location = loc
        obj.rotation_euler = rot
        # Rotation order is roll (Z), then pitch (X), and lastly yaw (Y)
        obj.rotation_mode = "ZXY"
        obj.scale = scale

        if "SetLodData" in mac_commands:
            # TODO LOD
            print("Skipping LOD entry in MAC file!")

        if "SetSurface" in mac_commands:
            srf_name = mac_commands["SetSurface"][1].strip('"')
            srf_data = get_loaded_data_safe(srf_name, srf_data_dict)
            load_srf(srf_data, obj.data)

        ob_armature = ""
        if "SetSkeleton" in mac_commands:
            skl_name = mac_commands["SetSkeleton"].strip('"')
            skl_data = get_loaded_data_safe(skl_name, skl_data_dict)
            ob_armature = hook_up_skl_to_obj(obj, skl_name, skl_data, collection)
            ob_armature.location = loc
            ob_armature.rotation_euler = rot
            ob_armature.scale = scale

        # Load vertex animation data as shape keys
        has_vertex_anim = False
        if "FRMB" in cpj_data and "AddFrames" in mac_commands and "NULL" in mac_commands["AddFrames"]:
            for frm_byte_data in cpj_data["FRMB"]:
                frm_data = Frm.from_bytes(frm_byte_data)

                load_frm(frm_data, obj)
                has_vertex_anim = True

        # Load in all animaiton sequences
        if "SEQB" in cpj_data and "AddSequences" in mac_commands and "NULL" in mac_commands["AddSequences"]:
            if not has_vertex_anim:
                obj = ""
            for seq_byte_data in cpj_data["SEQB"]:
                seq_data = Seq.from_bytes(seq_byte_data)

                load_seq(seq_data, obj, ob_armature, False)

    return {'FINISHED'}

def load_frm(frm_data, obj):
    verts = obj.data.vertices

    if obj.data.shape_keys == None or (not "Basis" in obj.data.shape_keys.key_blocks):
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
                pos = (vert.x, vert.y, vert.z)

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

    create_custom_data_layers(mesh_data)

    lod_lock_layer = mesh_data.attributes["lod_lock"]
    group_index_layer = mesh_data.attributes["frm_group_index"]

    for i, vert in enumerate(verts):
        # As 'flags' can only be 0 or 1, we don't need to do any type casting
        lod_lock_layer.data[i].value = vert.flags
        group_index_layer.data[i].value = vert.group_index

    print("mounts on geo object: " + str(len(geo_data.data_block.mounts)))
    return mesh_data, geo_data.data_block.mounts

def create_mesh_obj(name, collection, geo_data):
    mesh_data = geo_data[0]
    geo_mounts = geo_data[1]

    obj = bpy.data.objects.new(name, mesh_data)
    scene = bpy.context.scene
    collection.objects.link(obj)

    for mount in geo_mounts:
        # Create an "Empty" type object as a mount
        mount_obj = bpy.data.objects.new(mount.name, None)
        collection.objects.link(mount_obj)

        # Setup the partent
        parent_tri = mesh_data.polygons[mount.tri_index]

        mount_obj.parent = obj
        mount_obj.parent_type = 'VERTEX_3'
        mount_obj.parent_vertices = parent_tri.vertices

        # Calcute how much to move the mount point from the parent face center
        v0 = mesh_data.vertices[parent_tri.vertices[0]]
        v1 = mesh_data.vertices[parent_tri.vertices[1]]
        v2 = mesh_data.vertices[parent_tri.vertices[2]]

        # NOTE we need to reverse the vertex order here (IE 2,1,0 instead of 0,1,2)
        # because we changed the winding of the triangle when we imported the mesh (to fix the mesh normals).
        mount_loc = v2.co * mount.tri_barys.x + v1.co * mount.tri_barys.y + v0.co * mount.tri_barys.z

        # The mounts local tranform matrix is calculated by:
        # 1. Using the triangle normal as the "Up" axis
        # 2. Forward axis that is the direction from mount_loc to the first vertex in the triangle (v2 in this case because we changed the winding)
        # 3. The last axis is determined by crossing the to axis vectors above

        # Up
        z_vec = parent_tri.normal
        # Forward
        y_vec = -(v2.co - mount_loc)
        y_vec.normalize()
        # Side
        x_vec = y_vec.cross(z_vec)
        x_vec.normalize()

        mount_local_matrix = mathutils.Matrix([x_vec, y_vec, z_vec]).transposed()

        # Make sure that "matrix_world" is up to date.
        # We need to make sure that the mount point has been moved into the origin of Blenders triangle matrix transform space.
        # Otherwise we can't figure out how to manipulate the matrix_parent_inverse matrix to get to correct transform.
        bpy.context.view_layer.update()

        mat_world_inv = mount_obj.matrix_world.inverted()
        local_coords = mat_world_inv @ mount_loc

        matrix_diff = mat_world_inv.to_3x3() @ mount_local_matrix

        mount_obj.matrix_parent_inverse = matrix_diff.to_4x4()

        quat = mathutils.Quaternion((mount.base_rotate.s, mount.base_rotate.v.x, -mount.base_rotate.v.z, mount.base_rotate.v.y))
        rot_mat = quat.to_matrix().to_4x4()

        mount_obj.matrix_parent_inverse = mount_obj.matrix_parent_inverse @ rot_mat

        # Specify the offset from parent face center
        # NOTE we don't set the third axis (Z) here because we should always lie in the triangle plane, so it should always be zero.
        mount_obj.matrix_parent_inverse[0][3] = local_coords[0]
        mount_obj.matrix_parent_inverse[1][3] = local_coords[1]

        mount_obj.location.x = mount.base_translate.x
        mount_obj.location.y = -mount.base_translate.z
        mount_obj.location.z = mount.base_translate.y

        #mount_obj.scale[0] = mount.base_scale.x
        #mount_obj.scale[1] = -mount.base_scale.z
        #mount_obj.scale[2] = mount.base_scale.y

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

def process_bone(bone_index, created_bones, edit_bones, bone_datas, has_processed_parents):
    bone_data = bone_datas[bone_index]

    parent_index = bone_data.parent_index
    bone = edit_bones[created_bones[bone_index]]

    if parent_index >= 0:  # -1 is root bone/no parent
        parent_bone = edit_bones[created_bones[parent_index]]
        bone.parent = parent_bone

        if has_processed_parents[parent_index] == False:
            # Ensure that root parent bone is in the correct position.
            process_bone(parent_index, created_bones, edit_bones, bone_datas, has_processed_parents)

        # Set position to partent bone.
        # The relative transform will be handled in pose mode in a later step.
        bone.head = parent_bone.head
    else:
        # Set root bone position.
        # We need to do it here because otherwise the child bone transform
        # relations will not be correct.
        bhv = bone_data.base_translate
        bone.head = (bhv.x, -bhv.z, bhv.y)

    has_processed_parents[bone_index] = True
    bone.tail = bone.head + mathutils.Vector((0.0, 0.0, 1.0))
    bone.length = bone_data.length

# Load skeleton bones as blender armatures
def load_skl(skl_data):
    # Bones are handled in multiple passes since their
    # transforms are parent sensitive
    name = "No_name_defined"

    if hasattr(skl_data, 'name'):
        name = skl_data.name

    armature_data = bpy.data.armatures.new(name)
    ob_armature = bpy.data.objects.new(name, armature_data)

    scene = bpy.context.scene
    scene.collection.objects.link(ob_armature)
    bpy.context.view_layer.objects.active = ob_armature

    # We need to save the bone names in an list to ensure their index is preserved.
    # Blender will rearrange the bone arrays when parenting bones.
    # So the root bone will always be index zero and so on.
    created_bones = []

    bone_datas = skl_data.data_block.bones

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    edit_bones = ob_armature.data.edit_bones

    # Pass 1: Create bones and vertex groups
    for bone_data in bone_datas:
        edit_bone = edit_bones.new(bone_data.name)
        # temp head and tail, these get set for real
        # once the parent is set
        edit_bone.head = (0, 0, 0)
        edit_bone.tail = (0, 0, 1)

        # Save name here as the edit_bone variable will point to an invalid bone when Blender automatically shuffles the bone order
        created_bones.append(edit_bone.name)

    # Pass 2: Set bone parents
    has_processed_parents = [False] * len(bone_datas)

    for bone_index in range(len(bone_datas)):
        process_bone(bone_index, created_bones, edit_bones, bone_datas, has_processed_parents)

    bpy.ops.object.mode_set(mode='POSE', toggle=False)
    # Pass 3: Transform bones
    for bone_index, bone_data in enumerate(bone_datas):

        bone_name = created_bones[bone_index]

        pose_bone = ob_armature.pose.bones[bone_name]

        if pose_bone.parent != None:
            # We have already set the correct position for non parented bones.
            # So only set the location for bones that have parents here.
            bone_trans = bone_data.base_translate
            pose_bone.location = (bone_trans.x, bone_trans.y, bone_trans.z)

        # Recreating quat in a way blender recognizes
        bone_quat = mathutils.Quaternion((
            bone_data.base_rotate.s,
            bone_data.base_rotate.v.x,
            bone_data.base_rotate.v.y,
            bone_data.base_rotate.v.z
        ))

        pose_bone.rotation_quaternion = bone_quat

        bone_scl = bone_data.base_scale
        pose_bone.scale = (bone_scl.x, bone_scl.y, bone_scl.z)

    # Finally, set current pose as rest pose
    bpy.ops.pose.armature_apply(selected=False)

    # Pass 4: Try to connect bones that are in range of each other
    # This breaks animations, especially translations because we change the direction the bone points to
    #bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    #for bone in edit_bones:
    #    if bone.parent != None:
    #        vec = bone.parent.head - bone.head
    #        if abs(vec.length - bone.parent.length) < 0.001:
    #            bone.parent.tail = bone.head
    #            bone.use_connect = True

    ## Align tails of bones at the end of a bone chain
    #for bone in edit_bones:
    #    if not bone.use_connect:
    #        continue

    #    children_connected = False
    #    for child_bone in bone.children:
    #        if child_bone.use_connect:
    #            children_connected = True
    #            break

    #    if children_connected:
    #        continue

    #    old_length = bone.length
    #    vec = bone.head - bone.parent.head
    #    bone.tail = bone.head + vec
    #    bone.length = old_length

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    # Remove armature object, we will create it later with the MAC data
    bpy.data.objects.remove(ob_armature)
    print("mounts on skl object: " + str(len(skl_data.data_block.mounts)))

    vertex_data = skl_data.data_block.verts
    weight_data = skl_data.data_block.weights

    return (armature_data, created_bones, vertex_data, weight_data)

def hook_up_skl_to_obj(obj, name, skl_data, collection):
    armature_data = skl_data[0]
    created_bones = skl_data[1]
    vertex_data = skl_data[2]
    weight_data = skl_data[3]

    ob_armature = bpy.data.objects.new(name, skl_data[0])
    edit_bones = ob_armature.data.edit_bones

    scene = bpy.context.scene
    collection.objects.link(ob_armature)
    bpy.context.view_layer.objects.active = ob_armature

    # Create Vertex Groups and Weights
    for bone_name in created_bones:
        obj.vertex_groups.new(name=bone_name)

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    # We will create a base shape key to to store the shape described by the bone vertex offsets.
    # NOTE that this assumes that there are not vertex animations if there is a skeleton.
    # Don't know if this is always true in the cannibal format or not...
    obj.shape_key_add(name='Basis')
    sk_arm = obj.shape_key_add(name='Armature offsets')
    sk_arm.value = 1.0
    obj.data.shape_keys.use_relative = True

    for vert_index, vertex in enumerate(obj.data.vertices):
        num_weights = vertex_data[vert_index].num_weights
        first_weight_idx =  vertex_data[vert_index].first_weight

        vert_co = mathutils.Vector((0.0, 0.0, 0.0))

        for group_offset in range(num_weights):
            weight = weight_data[first_weight_idx + group_offset]

            group_name = created_bones[weight.bone_index]
            bone = edit_bones[group_name]

            vg = obj.vertex_groups.get(group_name)
            vg.add((vert_index,), weight.weight_factor, 'REPLACE')

            off_pos = weight.offset_pos
            vec = mathutils.Vector((off_pos.x, off_pos.y, off_pos.z))

            # Convert coordniates to world space
            vec = bone.matrix @ vec

            if num_weights > 1:
                # Only mutiply by the weight if there is more than one weight group.
                vec = vec * weight.weight_factor

            vert_co += vec

        sk_arm.data[vert_index].co = vert_co

    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    # Pass 6: Mount Points
    # TODO
    # but that can be later

    # Hook up the armature to the mesh object
    mod = obj.modifiers.new("Armature", 'ARMATURE')
    mod.object = ob_armature
    ob_armature.show_in_front = True

    return ob_armature

def armature_seq(armature_obj, seq_data, ignore_non_existing_bones):
    armature_obj.animation_data_create()

    action = bpy.data.actions.new(seq_data.name)
    action.use_fake_user = True

    action["Framerate"] = seq_data.play_rate

    armature_obj.animation_data.action = action

    frames = seq_data.data_block.frames

    bone_info = seq_data.data_block.bone_info
    bone_rot_data = seq_data.data_block.bone_rotate
    bone_scale_data = seq_data.data_block.bone_scale
    bone_trans_data = seq_data.data_block.bone_translate

    scene = bpy.context.scene

    for i, frame in enumerate(frames):
        scene.frame_current = i

        for rot_idx in range(frame.num_bone_rotate):
            bone_rot = bone_rot_data[frame.first_bone_rotate + rot_idx]

            bone_name = bone_info[bone_rot.bone_index].name

            if ignore_non_existing_bones and bone_name not in armature_obj.pose.bones:
                continue

            bone = armature_obj.pose.bones[bone_name]

            # Convert values to radians
            # 32768 is 180 degrees in the compressed 16bit value from roll,pitch, and yaw.
            x = bone_rot.pitch * pi / 32768
            y = bone_rot.yaw * pi / 32768
            z = bone_rot.roll * pi / 32768

            # Order of rotation is:
            # 1. Roll (Z)
            # 2. Pitch (X)
            # 3. Yaw (Y)
            euler_rot = mathutils.Euler((x,y,z), 'ZXY')
            bone.rotation_quaternion = euler_rot.to_quaternion()

            bone.keyframe_insert("rotation_quaternion")

        for scale_idx in range(frame.num_bone_scale):
            bone_scale = bone_scale_data[frame.first_bone_scale + scale_idx]

            bone_name = bone_info[bone_scale.bone_index].name

            if ignore_non_existing_bones and bone_name not in armature_obj.pose.bones:
                continue

            bone = armature_obj.pose.bones[bone_name]

            scale = bone_scale.scale
            bone.scale = (scale.x, scale.y, scale.z)

            bone.keyframe_insert("scale")

        for trans_idx in range(frame.num_bone_translate):
            bone_trans = bone_trans_data[frame.first_bone_translate + trans_idx]

            bone_name = bone_info[bone_trans.bone_index].name

            if ignore_non_existing_bones and bone_name not in armature_obj.pose.bones:
                continue

            bone = armature_obj.pose.bones[bone_name]

            trans = bone_trans.translate
            bone.location = (trans.x, trans.y, trans.z)

            bone.keyframe_insert("location")

    action.use_frame_range = True
    # There is no way to know if the animation is intended to be cyclic, but just assume this is the case.
    action.use_cyclic = True
    action.frame_start = 0
    action.frame_end = i

    return action

def add_action_events(action, events):
    # TODO: only trigger and triflag events are currently supported
    if len(events) == 0:
        return

    triflag_events = 0

    for event in events:
        if event.event_type == "TRIG":
            # Event triggers
            pose_mark = action.pose_markers.new(event.param_str)
            pose_mark.frame = round(action["Framerate"] * event.time)
        elif event.event_type == "TFLG":
            # Event triangle flag manipulation
            event_name = f"TFLG{triflag_events}"
            pose_mark = action.pose_markers.new(event_name)
            pose_mark.frame = round(action["Framerate"] * event.time)
            action[event_name] = event.param_str 
            triflag_events = triflag_events + 1
        else:
            raise ImportError(f"Event type {event.event_type} is not yet supported...")

def load_seq(seq_data, obj, armature_obj, ignore_non_existing_bones):
    # TODO only create animation data for skeleton/shape keys if the animations has any keys for them

    if len(seq_data.data_block.frames) == 0:
        # Some files (like EDF_FrameTest.cpj) has broken sequence data in them.
        # IE sequences with no frames
        return

    action = None

    if armature_obj != "":
        action = armature_seq(armature_obj, seq_data, ignore_non_existing_bones)

    if obj == "":
        add_action_events(action, seq_data.data_block.events)
        return

    # Handle vertex animations
    obj_key_data = obj.data.shape_keys
    obj_key_data.animation_data_create()

    if action == None:
        action = bpy.data.actions.new(seq_data.name)
        action.use_fake_user = True

        action["Framerate"] = seq_data.play_rate

    obj_key_data.animation_data.action = action

    frames = seq_data.data_block.frames

    scene = bpy.context.scene

    for i, frame in enumerate(frames):
        scene.frame_current = i

        if frame.offset_vert_frame_name == -1:
            # No vertex frame data here
            continue

        if not frame.vert_frame_name in obj_key_data.key_blocks:
            # Some files like EDF1.cpj has lingering vertex frame animation data but no
            # vertex frames to go with them.
            continue

        shape_key = obj_key_data.key_blocks[frame.vert_frame_name]

        obj_key_data.eval_time = shape_key.frame
        obj_key_data.keyframe_insert("eval_time")

    action.use_frame_range = True
    # There is no way to know if the animation is intended to be cyclic, but just assume this is the case.
    action.use_cyclic = True
    action.frame_start = 0
    action.frame_end = i

    add_action_events(action, seq_data.data_block.events)

def load_mac(mac_data):
    autoexec_commands = {}

    allowed_dupes = ["AddFrames", "AddSequences"]

    mac_text = bpy.data.texts.new("cpj_" + mac_data.name)
    for sec in mac_data.data_block.sections:
        # Write section name start delimiter
        mac_text.write("--- " + sec.name + "\n")

        start_com = sec.first_command
        end_com = start_com + sec.num_commands
        for com in mac_data.data_block.commands[start_com:end_com]:
            mac_text.write(com.command_str + "\n")

        if sec.name == "autoexec":
            for com in mac_data.data_block.commands[start_com:end_com]:
                data = com.command_str.split()

                if len(data) == 2:
                    com_data = data[1].strip('"')
                else:
                    com_data = data[1:]

                is_list = data[0] in allowed_dupes

                if data[0] in autoexec_commands:
                    if is_list:
                        autoexec_commands[data[0]].append(com_data)
                    else:
                        raise ImportError("Unexpected duplicate command '" + data[0] + "' in mac file: " + mac_data.name)
                else:
                    if is_list:
                        autoexec_commands[data[0]] = [com_data]
                    else:
                        autoexec_commands[data[0]] = com_data

    return autoexec_commands
