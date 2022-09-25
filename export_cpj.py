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
import struct
import bpy

from mathutils import Vector
from mathutils import Matrix
import mathutils
import bmesh

from cpj_utils import *

# ----------------------------------------------------------------------------
def quat_to_cpj_quat(quat):
    # cpj_quat = x,y,z,w
    cpj_quat = [quat[1], quat[2], quat[3], quat[0]]
    return cpj_quat

def save(context, filepath):

    apply_modifiers = True

    data_chunks = []

    objs_to_process = []

    for text_block in bpy.data.texts:
        if text_block.name.startswith("cpj_"):
            mac_name = text_block.name[4:]
            mac_data = parse_mac_text(mac_name, text_block.as_string(), text_block.name)
            data_chunks.append(mac_data[0])
            objs_to_process.append(mac_data[1:])

    for obj_data in objs_to_process:
        obj = bpy.data.objects[obj_data[0]]
        if apply_modifiers:
            depsgraph = context.evaluated_depsgraph_get()
            me = obj.evaluated_get(depsgraph).to_mesh()
        else:
            me = obj.to_mesh()

        bm = bmesh.new()
        bm.from_mesh(me)

        # The cpj format only supports triangles, so ensure that everything is triangulated
        bmesh.ops.triangulate(bm, faces=bm.faces)
        loops = sum(bm.calc_loop_triangles(),())

        data_chunks.append(create_geo_data(obj, me.name, bm, loops, True))

        if len(obj_data[1]) > 1:
            raise Exception("Can't handle more that one SRF layer on a mesh currently")

        for uv_name in obj_data[1]:
            data_chunks.append(create_srf_data(obj, uv_name, bm, loops))
        bm.free()

        if obj_data[2] != "":
            armature = bpy.data.objects[obj_data[2]]
            data_chunks.append(create_skl_data(obj, me, armature))

        if apply_modifiers:
            obj.evaluated_get(depsgraph).to_mesh_clear()
        else:
            me = obj.to_mesh_clear()

    write_cpj_file(filepath, data_chunks)

    return {'FINISHED'}

def parse_mac_text(mac_name, mac_text, text_block_name):
    # Split up the commands into a list
    command_list = mac_text.splitlines()
    # If there are multiple newlines after each other we will have empty commands, filter those out
    command_list = list(filter(None, command_list))
    list_size = len(command_list)

    if list_size == 0:
        raise Exception("Invalid MAC text command file supplied: " + text_block_name)

    # Data for the mac byte data creator
    section_data = []
    command_strings = []

    command_index = 0
    list_index = 0

    mesh_object_name = ""
    armature_name = ""
    uv_names = []
    found_primary_uv = False
    has_frames = False
    has_seq = False
    has_author = False
    has_descripton = False

    valid_autoexec_commands = ["SetAuthor", "SetDescription", "SetGeometry", "SetLodData", "SetSkeleton", "SetSurface", "AddFrames", "AddSequences"]
    # TODO remake this list to be exclusive, IE which types NOT to check when automatic origin and scale etc writing is implemented
    quote_check = ["SetAuthor", "SetDescription", "SetGeometry", "SetLodData", "SetSkeleton", "AddFrames", "AddSequences"]

    # Go through all command sections
    while list_index < list_size:
        section_name = command_list[list_index].split()

        if len(section_name) != 2 and section_name[0] != "---":
            raise Exception("Invalid section in MAC text command file: " + text_block_name)

        list_index +=1

        num_commands = 0
        first_command = command_index

        # Go trough all of the commands in this section
        while list_index < list_size:
            command = command_list[list_index]
            if command.startswith("---"):
                # New command section
                break

            if section_name[1] == "autoexec":
                com = command.split()

                # TODO uncomment this once we have automatic Origin, scale etc implemented
                #if not com[0] in valid_autoexec_commands:
                #    raise Exception(command + " is not a valid autoexec command!")

                if len(com) < 2:
                    raise Exception("Too few arguments for command in MAC text command file: " + text_block_name + "\n Command was: " + command)

                if com[0] in quote_check:
                    if not (com[1].startswith('"') and com[1].endswith('"')):
                        raise Exception("Error in: " + text_block_name + "\n" + com[0] + " requires the string argument to be in quotation marks")

                match com[0]:
                    case "SetGeometry":
                        mesh_object_name = com[1].strip('"')
                        if not mesh_object_name in bpy.data.objects:
                            raise Exception("Error in: " + text_block_name + "\n 'SetGeometry' object " + mesh_object_name + " does not exist")
                        if bpy.data.objects[mesh_object_name].type != 'MESH':
                            raise Exception("Error in: " + text_block_name + "\n 'SetGeometry' object " + mesh_object_name + " is not a mesh" )
                        # TODO write in all the special sections like Orgin, Scale, boundingboxes etc.
                    case "SetSurface":
                        if len(com) < 3:
                            raise Exception("Error in: " + text_block_name + "\n 'SetSurface' requires two arguments. Index and uv name")
                        if not com[1].isnumeric():
                            raise Exception("Error in: " + text_block_name + "\n 'SetSurface', the first argument has to be number")
                        if not (com[2].startswith('"') and com[2].endswith('"')):
                            raise Exception("Error in: " + text_block_name + "\n 'SetGeometry' requires the object name to be in quotation marks")

                        if com[1] == "0":
                            found_primary_uv = True
                        uv_names.append(com[2].strip('"'))
                    case "SetSkeleton":
                        armature_name = com[1].strip('"')
                        if not armature_name in bpy.data.objects:
                            raise Exception("Error in: " + text_block_name + "\n 'SetSkeleton' object " + armature_name + " does not exist")
                        if bpy.data.objects[armature_name].type != 'ARMATURE':
                            raise Exception("Error in: " + text_block_name + "\n 'SetSkeleton' object " + armature_name + " is not an armature" )
                    case "SetAuthor":
                        has_author = True
                    case "SetDescription":
                        has_descripton = True
                    case "AddFrames":
                        has_frames = True
                    case "AddSequences":
                        has_seq = True
                    case "SetLodData":
                        print("Skipping LOD entry in MAC file!")
                        list_index +=1
                        continue

            command_strings.append(command)

            num_commands += 1
            list_index +=1
            command_index += 1

        sec_data = [section_name[1], num_commands, first_command]
        section_data.append(sec_data)

    # Sanity checks
    if mesh_object_name == "":
        raise Exception("No mesh object specified in MAC text command file: " + text_block_name)

    if len(uv_names) == 0:
        raise Exception("No UV was specified in MAC text command file: " + text_block_name)
    if not found_primary_uv:
        raise Exception("No primary UV was specified in MAC test command file: " + text_block_name)
    for uv_name in uv_names:
        if not uv_name in bpy.data.objects[mesh_object_name].data.uv_layers:
            raise Exception(uv_name + " does not exist on the specifed mesh object in MAC command file: " + text_block_name)

    if not has_frames:
        raise Exception("'AddFrames' was not specified in MAC text command file: " + text_block_name)
    if not has_seq:
        raise Exception("'AddSequences' was not specified in MAC text command file: " + text_block_name)
    if not has_author:
        raise Exception("'SetAuthor' was not specified in MAC text command file: " + text_block_name)
    if not has_descripton:
        raise Exception("'SetDescription' was not specified in MAC text command file: " + text_block_name)

    mac_byte_data = create_mac_byte_array(mac_name, section_data, command_strings)

    return (mac_byte_data, mesh_object_name, uv_names, armature_name)

def get_geo_mount_data(obj, bm):
    mounts = []
    mounts_data = []
    for child in obj.children:
        if child.type == 'EMPTY' and child.parent_type == 'VERTEX_3':
            mounts.append(child)

    obj_mat_inv = obj.matrix_world.inverted()

    for mount in mounts:
        # Get triangle to the mount point
        v0 = bm.verts[mount.parent_vertices[0]]
        v1 = bm.verts[mount.parent_vertices[1]]
        v2 = bm.verts[mount.parent_vertices[2]]

        face_set = set( v0.link_faces ) & set( v1.link_faces ) & set( v2.link_faces )

        if len(face_set) != 1:
            raise Exception("Invalid geo mount in object '" + obj.name + "', not parented to a single triangle.")
        face = face_set.pop()

        # Convert mount location and axis into mesh local coordinates
        mount_mat = obj_mat_inv @ mount.matrix_world
        mount_loc = mount_mat.translation

        point_offset = Vector((0,0,0))

        if bmesh.geometry.intersect_face_point(face, mount_loc):
            # The projected point will lie inside the triangle
            vec = mount_loc - v2.co
            vec_normal = vec.project(face.normal)

            point_in_plane = vec - vec_normal + v2.co

            bary_weights = mathutils.interpolate.poly_3d_calc([v2.co,v1.co,v0.co], point_in_plane)

            if vec_normal.length > 0.001:
                point_offset = mount_loc - point_in_plane
        else:
            # The point will have to be projected to the closest edge
            min_dist = float("inf")

            edge_corners = [v2.co,v1.co,v0.co]
            for i, co in enumerate(edge_corners):
                e_vec = edge_corners[(i+1) % 3] - edge_corners[i]

                mount_vec = mount_loc - edge_corners[i]
                proj_e = mount_vec.project(e_vec)
                dist = (mount_vec - proj_e).length
                if dist < min_dist:
                    min_dist = dist
                    bary_weights = [0,0,0]

                    loc_on_edge = mount_vec.dot(e_vec) / e_vec.dot(e_vec)
                    if loc_on_edge <= 0:
                        bary_weights[i] = 1
                        point_in_plane = edge_corners[i]
                    elif loc_on_edge >= 1:
                        bary_weights[(i+1) % 3] = 1
                        point_in_plane = edge_corners[(i+1) % 3]
                    else:
                        bary_weights[i] = 1 - loc_on_edge
                        bary_weights[(i+1) % 3] = loc_on_edge
                        point_in_plane = proj_e + edge_corners[i]

                    point_offset = mount_loc - point_in_plane
        # Calculate the "native" transform axis the cpj mount will use
        # Up
        z_vec = face.normal
        # Forward
        y_vec = -(v2.co - point_in_plane)
        y_vec.normalize()
        # Side
        x_vec = y_vec.cross(z_vec)
        x_vec.normalize()

        mount_local_matrix = Matrix([x_vec, y_vec, z_vec]).transposed()

        # Calculate the amount of rotation needed to get from the "native" cpj transform to have the axis line up with the mount point axis.
        mount_rot = mount_mat.to_quaternion()
        cpj_rot = mount_local_matrix.to_quaternion()
        rot_diff = cpj_rot.rotation_difference(mount_rot)
        # Convert into cpj transform space
        rot_diff = [rot_diff.w, rot_diff.x, rot_diff.z, -rot_diff.y]

        mount_mat_3x3 = mount_mat.to_3x3()

        if point_offset.length < 0.001:
            mount_local_translation = [0,0,0]
        else:
            # Convert to cpj "Y up" coordinates.
            mount_local_translation = [point_offset.dot(mount_mat_3x3.col[0]),
                                       point_offset.dot(mount_mat_3x3.col[2]),
                                       -point_offset.dot(mount_mat_3x3.col[1])]

        mount_data = []
        mount_data.append(mount.name)
        mount_data.append(face.index)
        mount_data.append(bary_weights)
        mount_data.append((1, 1, 1))
        mount_data.append(quat_to_cpj_quat(rot_diff))
        mount_data.append(mount_local_translation)

        mounts_data.append(mount_data)
    return mounts_data

def create_geo_data(obj, geo_name, bm, loops, apply_modifiers):
    # Ensure all indices are valid and up to date
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # The loop indices are invalid after triangulation, fix them.
    for i, loop in enumerate(loops):
        loop.index = i

    # construct geo data lists
    verts = []
    edges = []
    tris = []
    mounts = []
    obj_links = []

    flags_layer = bm.verts.layers.int['lod_lock']
    group_index_layer = bm.verts.layers.int['frm_group_index']

    for vert_data in bm.verts:
        vert = []
        vert.append(vert_data[flags_layer])
        vert.append(vert_data[group_index_layer])
        vert.append(0) # reserved, must be zero
        vert.append(len(vert_data.link_loops)) # num_edge_links
        vert.append(len(vert_data.link_faces)) # num_tri_links

        # Save the start index that we wrote data to in obj_links
        vert.append(len(obj_links)) # first_edge_link
        for loop in vert_data.link_loops:
            obj_links.append(loop.index)

        vert.append(len(obj_links)) # first_tri_link
        for face in vert_data.link_faces:
            obj_links.append(face.index)
        # We need to flip the coordinate axis as Blender and CPJ doesn't use the same system
        vert.append((vert_data.co.x, vert_data.co.z, -vert_data.co.y)) # ref_pos

        verts.append(vert)

    for loop in loops:
        edge = []
        edge.append(loop.link_loop_next.vert.index) # head_vertex
        edge.append(loop.vert.index) # tail_vertex
        edge.append(loop.link_loop_radial_next.index) # inverted edge
        edge.append(len(loop.link_loops) + 1) # num_tri_links
        edge.append(len(obj_links)) # first_tri_link

        obj_links.append(loop.face.index)
        for i in range(len(loop.link_loops)):
            loop = loop.link_loop_radial_next
            obj_links.append(loop.face.index)

        edges.append(edge)

    for tri_data in bm.faces:
        tri = []
        edge_ring = tri_data.loops
        # We need to reverse the winding to be able to properly transform into the CPJ coordinate system.
        tri.append((edge_ring[2].index, edge_ring[1].index, edge_ring[0].index)) # edge_ring
        tri.append(0) # reserved, must be zero

        tris.append(tri)

    mounts = get_geo_mount_data(obj, bm)

    geo_byte_data = create_geo_byte_array(geo_name, verts, edges, tris, mounts, obj_links)

    return geo_byte_data

def create_srf_data(obj, uv_name, bm, loops):
    # This should have already been checked in the MAC data parser, but can't hurt to be a bit paranoid
    if not uv_name in bm.loops.layers.uv:
        raise Exception("The specifed UV '" + uv_name + "' doesn't exist in object: " + obj.name )

    # construct srf data lists
    textures = []
    tris = []
    uv_coords = []

    # TODO this only works properly with one UV mat.
    # we don't know which textures to pull and we can't have mutiple data layers of the same name for the mesh.
    for material in obj.data.materials:
        ref_name = ""
        if "CPJ texture ref" in material:
            ref_name = material["CPJ texture ref"]
        tex = [material.name, ref_name]
        textures.append(tex)

    flags_layer = bm.faces.layers.int['flags']
    smooth_group_layer = bm.faces.layers.int['smooth_group']
    alpha_level_layer = bm.faces.layers.int['alpha_level']
    glaze_index_layer = bm.faces.layers.int['glaze_index']
    glaze_func_layer = bm.faces.layers.int['glaze_func']

    for tri_data in bm.faces:
        tri = []
        # We need to reverse the winding to be able to properly transform into the CPJ coordinate system.
        tri.append((tri_data.loops[2].index, tri_data.loops[1].index, tri_data.loops[0].index))
        tri.append(tri_data.material_index)
        tri.append(0) # reserved, must be zero
        tri.append(tri_data[flags_layer])
        tri.append(tri_data[smooth_group_layer])
        tri.append(tri_data[alpha_level_layer])
        tri.append(tri_data[glaze_index_layer])
        tri.append(tri_data[glaze_func_layer])

        tris.append(tri)

    uv_layer = bm.loops.layers.uv[0]

    for loop in loops:
        uv = loop[uv_layer].uv
        # The texture coordinate system is different in CPJ.
        # The upper left corner is the origin point (instead of the bottom left as it is in Blender)
        uv_coords.append((uv[0], 1.0 - uv[1]))

    srf_byte_data = create_srf_byte_array(uv_name, textures, tris, uv_coords)

    return srf_byte_data

def create_skl_data(obj, me, arm_obj):
    bone_list = arm_obj.data.bones

    bones = []

    # Ensure that the armature is in its rest postion
    old_pose_setting = arm_obj.data.pose_position
    arm_obj.data.pose_position = 'REST'

    for bone_data in bone_list:
        bone = []

        mat = bone_data.matrix_local

        if bone_data.parent == None:
            # The base transform matrix for a bone in Blender
            base_mat = Matrix()
            base_mat[1][1] = 0
            base_mat[1][2] = -1

            base_mat[2][1] = 1
            base_mat[2][2] = 0

            parent_index = -1
        else:
            base_mat = bone_data.parent.matrix_local
            parent_index = bone_list.find(bone_data.parent.name)

        diff_mat = base_mat.inverted() @ bone_data.matrix_local
        decomp = diff_mat.decompose()
        bone_trans = decomp[0]

        bone.append(bone_data.name)
        bone.append(parent_index)
        bone.append(decomp[2]) # base_scale
        bone.append(quat_to_cpj_quat(decomp[1])) # base_rotation (cpj quaternion)
        bone.append(bone_trans) # base_translation
        bone.append(bone_data.length)

        bones.append(bone)

    verts = []
    weights = []

    for vert_data in me.vertices:
        vert = []
        vert.append(len(vert_data.groups)) # num_weights
        vert.append(len(weights)) # first_weight

        verts.append(vert)

        for group in vert_data.groups:
            weight_data = []

            bone_name = obj.vertex_groups[group.group].name
            bone_index = bone_list.find(bone_name)
            bone = bone_list[bone_index]
            offset_pos = bone.matrix_local.inverted() @ vert_data.co

            weight_data.append(bone_index)
            weight_data.append(group.weight) # weight_factor
            weight_data.append(offset_pos)

            weights.append(weight_data)

    # TODO mounts
    mounts = []

    skl_byte_data = create_skl_byte_array(arm_obj.name, bones, verts, weights, mounts)

    arm_obj.data.pose_position = old_pose_setting

    return skl_byte_data

def calc_boundbox_max_min(obj):
    # Ensure that the bounding box corners are in world space coordinates
    bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    max_x = -float("inf")
    min_x = float("inf")

    max_y = -float("inf")
    min_y = float("inf")

    max_z = -float("inf")
    min_z = float("inf")

    for corner in bbox_corners:
        max_x = max(max_x, corner.x)
        min_x = min(min_x, corner.x)
        # Switch around coordinate system because it is different in CPJ
        max_y = max(max_y, corner.z)
        min_y = min(min_y, corner.z)
        max_z = max(max_z, -corner.y)
        min_z = min(min_z, -corner.y)

    max_bb = [max_x, max_y, max_z]
    min_bb = [min_x, min_y, min_z]

    return max_bb, min_bb
