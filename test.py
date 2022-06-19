from cpj_utils import *

from formats.mac import Mac
from formats.srf import Srf

from compare_data import *

file_data1 = load_cpj_data("/tmp/ASHTRAY1.cpj")
#file_data2 = load_cpj_data("/tmp/smokealarm.cpj")

geo_data1 = Geo.from_bytes(file_data1["GEOB"][0])
#geo_data2 = Geo.from_bytes(file_data2["GEOB"][0])

#compare_data(geo_data1, geo_data2, "geo")

mac_data1 = Mac.from_bytes(file_data1["MACB"][0])
#mac_data2 = Mac.from_bytes(file_data2["MACB"][0])

#compare_data(mac_data1, mac_data2, "mac")

srf_data1 = Srf.from_bytes(file_data1["SRFB"][0])

byte_array_list = []

# construct a mac information data list
command_strings = []
for com in mac_data1.data_block.commands:
    command_strings.append(com.command_str)

mac_byte_data = create_mac_byte_array(mac_data1.name, command_strings)

parse_and_compare_data("MACB", file_data1["MACB"][0], mac_byte_data)

# construct geo data
verts = []
edges = []
tris = []
mounts = []
obj_links = []

for vert_data in geo_data1.data_block.vertices:
    vert = []
    vert.append(vert_data.flags)
    vert.append(vert_data.group_index)
    vert.append(vert_data.reserved)
    vert.append(vert_data.num_edge_links)
    vert.append(vert_data.num_tri_links)
    vert.append(vert_data.first_edge_link)
    vert.append(vert_data.first_tri_link)
    pos = vert_data.ref_pos
    vert.append((pos.x, pos.y, pos.z))

    verts.append(vert)

for edge_data in geo_data1.data_block.edges:
    edge = []
    edge.append(edge_data.head_vertex)
    edge.append(edge_data.tail_vertex)
    edge.append(edge_data.inverted_edge)
    edge.append(edge_data.num_tri_links)
    edge.append(edge_data.first_tri_link)

    edges.append(edge)

for tri_data in geo_data1.data_block.triangles:
    tri = []
    edge_ring = tri_data.edge_ring
    tri.append((edge_ring[0], edge_ring[1], edge_ring[2]))
    tri.append(tri_data.reserved)

    tris.append(tri)

for mount_data in geo_data1.data_block.mounts:
    mount = []
    mount.append(mount_data.name)
    mount.append(mount_data.tri_index)
    tri_barys = mount_data.tri_barys
    mount.append((tri_barys.x, tri_barys.y, tri_barys.z))
    base_scale = mount_data.base_scale
    mount.append((base_scale.x, base_scale.y, base_scale.z))
    base_rotate = mount_data.base_rotate
    mount.append((base_rotate.v.x, base_rotate.v.y, base_rotate.v.z, base_ratate.s))
    base_translate = mount_data.base_translate
    mount.append((base_translate.x, base_translate.y, base_translate.z))

    mounts.append(mount)

for obj_link_data in geo_data1.data_block.obj_links:
    obj_links.append(obj_link_data.link)

geo_byte_data = create_geo_byte_array(geo_data1.name, verts, edges, tris, mounts, obj_links)

parse_and_compare_data("GEOB", file_data1["GEOB"][0], geo_byte_data)

# construct a srf data list

textures = []
tris = []
uv_coords = []

for tex_data in srf_data1.data_block.textures:
    # TODO check if ref_name is missing
    tex = [tex_data.name, tex_data.ref_name]
    textures.append(tex)

for tri_data in srf_data1.data_block.tris:
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

for uv_data in srf_data1.data_block.uvs:
    uv_coords.append((uv_data.u, uv_data.v))

srf_byte_data = create_srf_byte_array(srf_data1.name, textures, tris, uv_coords)

parse_and_compare_data("SRFB", file_data1["SRFB"][0], srf_byte_data)

#for key in file_data1:
#    for byte_array in file_data1[key]:
#        byte_array_list.append(byte_array)
#

# Finally write the cpj file to disk
byte_array_list = [ mac_byte_data, geo_byte_data, srf_byte_data ]

write_cpj_file("/tmp/out.cpj", byte_array_list)

file_data2 = load_cpj_data("/tmp/out.cpj")

compare_cpj_data(file_data1, file_data2)
