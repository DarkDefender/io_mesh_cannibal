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
from formats.geo import Geo
from formats.srf import Srf
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

    mesh_data = load_geo(geo_data)

    if len(cpj_data["SRFB"]) > 1:
        raise Exception('Importing cpjs with more than one surface in it is not supported yet')
        return {'CANCELLED'}

    # Load in all surface data
    # TODO load in more than one SRF entry if there are any
    srf_data = Srf.from_bytes(cpj_data["SRFB"][0])

    load_srf(srf_data, mesh_data)

    # Load Model Actor Configuation data
    mac_data = Mac.from_bytes(cpj_data["MACB"][0])

    load_mac(mac_data)

    return {'FINISHED'}

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

    return mesh_data

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

