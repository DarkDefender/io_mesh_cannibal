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

import bmesh

# ----------------------------------------------------------------------------
def save(context, filepath):
    mesh_objs = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            mesh_objs.append(obj)


    if len(mesh_objs) > 1:
        raise Exception('Exporting cpjs with more than one mesh object in it is not supported yet')
        return {'CANCELLED'}

    data_chunks = []

    for obj in mesh_objs:
        if apply_modifiers:
            depsgraph = context.evaluated_depsgraph_get()
            me = ob.evaluated_get(depsgraph).to_mesh()
        else:
            me = ob.to_mesh()

        bm = bmesh.new()
        bm.from_mesh(me)
        data_chunks += create_geo_data(bm, True)
        data_chunks += create_srf_data(bm)
        bm.free()

        if apply_modifiers:
            ob.evaluated_get(depsgraph).to_mesh_clear()
        else:
            me = ob.to_mesh_clear()

    return {'FINISHED'}

def create_geo_data(bm, apply_modifiers):
    # The cpj format only supports triangles to ensure that everything is triangulated
    loops = bmesh.ops.triangulate(bm, faces=bm.faces)

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

    flags_layer = bl.verts.layers.int['lod_lock']
    group_index_layer = bl.verts.layers.int['frm_group_index']

    for vert_data in bm.verts:
        vert = []
        vert.append(vert_data[flags_layer])
        vert.append(vert_data[group_index_layer])
        vert.append(0) # reserved, must be zero
        vert.append(len(vert_data.link_loops)) # num_edge_links
        vert.append(len(vert_data.link_faces)) # num_tri_links

        # Save the start index that we wrote data to in obj_links
        vert.append(len(obj_links)) # first_edge_link
        for loop in vert_data.link_loop:
            obj_links.append(loop.index)

        vert.append(len(obj_links)) # first_tri_link
        for face in vert_data.link_face:
            obj_links.append(face.index)
        # We need to flip the coordinate axis as Blender and CPJ doesn't use the same system
        vert.append((vert_data.co.x, vert_data.co.z, -vert_data.co.y)) # ref_pos

        verts.append(vert)

    for loop in loops:
        edge = []
        edge.append(loop.link_loop_next.vert.index) # head_vertex
        edge.append(loop.vert.index) # tail_vertex
        edge.append(loop.link_loop_radial_next.index) # inverted edge
        edge.append(loop.link_loops + 1) # num_tri_links
        edge.append(len(obj_links)) # first_tri_link

        obj_links.append(loop.face.index)
        for i in range(loop.link_loops):
            loop = loop.link_loop_radial_next
            obj_links.append(loop.face.index)

        edges.append(edge)

    for tri_data in bm.faces:
        tri = []
        edge_ring = tri_data.loops
        tri.append((edge_ring[0].index, edge_ring[1].index, edge_ring[2].index)) # edge_ring
        tri.append(0) # reserved, must be zero

        tris.append(tri)

    # TODO
    #for mount_data in geo_data.data_block.mounts:
    #    mount = []
    #    mount.append(mount_data.name)
    #    mount.append(mount_data.tri_index)
    #    tri_barys = mount_data.tri_barys
    #    mount.append((tri_barys.x, tri_barys.y, tri_barys.z))
    #    base_scale = mount_data.base_scale
    #    mount.append((base_scale.x, base_scale.y, base_scale.z))
    #    base_rotate = mount_data.base_rotate
    #    mount.append((base_rotate.v.x, base_rotate.v.y, base_rotate.v.z, base_rotate.s))
    #    base_translate = mount_data.base_translate
    #    mount.append((base_translate.x, base_translate.y, base_translate.z))

    #    mounts.append(mount)

    geo_byte_data = create_geo_byte_array(geo_data.name, verts, edges, tris, mounts, obj_links)

    return geo_byte_data

def create_srf_data(bm):
    # construct srf data lists
    textures = []
    tris = []
    uv_coords = []

    for tex_data in srf_data.data_block.textures:
        # TODO check if ref_name is missing
        tex = [tex_data.name, tex_data.ref_name]
        textures.append(tex)

    for tri_data in srf_data.data_block.tris:
        tri = []
        uv_index = tri_data.uv_index
        tri.append((uv_index[0], uv_index[1], uv_index[2]))
        tri.append(tri_data.tex_index)
        tri.append(tri_data.reserved)
        tri.append(tri_data.flags)
        tri.append(tri_data.smooth_group)
        tri.append(tri_data.alpha_level)
        tri.append(tri_data.glaze_tex_index)
        tri.append(tri_data.glaze_func)

        tris.append(tri)

    for uv_data in srf_data.data_block.uvs:
        uv_coords.append((uv_data.u, uv_data.v))

    srf_byte_data = create_srf_byte_array(srf_data.name, textures, tris, uv_coords)

    return srf_byte_data
