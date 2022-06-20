from cpj_utils import *

from compare_data import *

file_data1 = load_cpj_data("/tmp/Edf_dog.cpj")
#file_data2 = load_cpj_data("/tmp/smokealarm.cpj")

#frm_data1 = Frm.from_bytes(file_data1["FRMB"][0])

geo_data1 = Geo.from_bytes(file_data1["GEOB"][0])
#geo_data2 = Geo.from_bytes(file_data2["GEOB"][0])

lod_data1 = Lod.from_bytes(file_data1["LODB"][0])

#compare_data(geo_data1, geo_data2, "geo")

mac_data1 = Mac.from_bytes(file_data1["MACB"][0])
#mac_data2 = Mac.from_bytes(file_data2["MACB"][0])

#compare_data(mac_data1, mac_data2, "mac")

srf_data1 = Srf.from_bytes(file_data1["SRFB"][0])

skl_data1 = Skl.from_bytes(file_data1["SKLB"][0])

# construct a vertex frame animation data list
#frames = []
#for frame_data in frm_data1.data_block.frames:
#    frame = []
#    frame.append(frame_data.name)
#    bb_min = frame_data.bb_min
#    frame.append((bb_min.x, bb_min.y, bb_min.z))
#    bb_max = frame_data.bb_max
#    frame.append((bb_max.x, bb_max.y, bb_max.z))
#
#    frame.append(frame_data.num_groups)
#    frame_groups = []
#    for group_data in frame_data.groups:
#        byte_scale = group_data.byte_scale
#        bs = (byte_scale.x, byte_scale.y, byte_scale.z)
#        byte_trans = group_data.byte_translate
#        bt = (byte_trans.x, byte_trans.y, byte_trans.z)
#        frame_groups.append((bs, bt))
#    frame.append(frame_groups)
#
#    frame.append(frame_data.num_verts)
#    frame_verts = []
#    for vert_data in frame_data.verts:
#        if (frame_data.num_groups == 0):
#            # Save uncompressed vert data
#            frame_verts.append((vert_data.x, vert_data.y, vert_data.z))
#            continue
#        # Save compressed data
#        pos = vert_data.pos
#        frame_verts.append((vert_data.group, (pos[0], pos[1], pos[2])))
#    frame.append(frame_verts)
#
#    frames.append(frame)
#
#frm_bb_min = (frm_data1.bb_min.x, frm_data1.bb_min.y, frm_data1.bb_min.z)
#frm_bb_max = (frm_data1.bb_max.x, frm_data1.bb_max.y, frm_data1.bb_max.z)
#
#frm_byte_data = create_frm_byte_array(frm_data1.name, (frm_bb_min, frm_bb_max), frames)
#
#parse_and_compare_data("FRMB", file_data1["FRMB"][0], frm_byte_data)

# construct a mac information data list
command_strings = []
for com in mac_data1.data_block.commands:
    command_strings.append(com.command_str)

mac_byte_data = create_mac_byte_array(mac_data1.name, command_strings)

parse_and_compare_data("MACB", file_data1["MACB"][0], mac_byte_data)

# construct geo data lists
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
    mount.append((base_rotate.v.x, base_rotate.v.y, base_rotate.v.z, base_rotate.s))
    base_translate = mount_data.base_translate
    mount.append((base_translate.x, base_translate.y, base_translate.z))

    mounts.append(mount)

for obj_link_data in geo_data1.data_block.obj_links:
    obj_links.append(obj_link_data.link)

geo_byte_data = create_geo_byte_array(geo_data1.name, verts, edges, tris, mounts, obj_links)

parse_and_compare_data("GEOB", file_data1["GEOB"][0], geo_byte_data)

# construct srf data lists

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

# construct lod data lists

levels = []
tris = []
vert_relay = []

for level_data in lod_data1.data_block.levels:
    level = []
    level.append(level_data.detail)
    level.append(level_data.num_tri)
    level.append(level_data.num_vert_relay)
    level.append(level_data.first_tri)
    level.append(level_data.first_vert_relay)

    levels.append(level)

for tris_data in lod_data1.data_block.tris:
    tri = []
    tri.append(tris_data.tri_index)
    vert_idx = tris_data.vert_index
    tri.append((vert_idx[0], vert_idx[1], vert_idx[2]))
    uv_idx = tris_data.uv_index
    tri.append((uv_idx[0], uv_idx[1], uv_idx[2]))

    tris.append(tri)

for vert_relay_data in lod_data1.data_block.vert_relay:
    vert_relay.append(vert_relay_data)

lod_byte_data = create_lod_byte_array(lod_data1.name, levels, tris, vert_relay)

parse_and_compare_data("LODB", file_data1["LODB"][0], lod_byte_data)

# construct a skl data lists

bones = []
verts = []
weights = []
mounts = []

for bone_data in skl_data1.data_block.bones:
    bone = []
    bone.append(bone_data.name)
    bone.append(bone_data.parent_index)
    base_scale = bone_data.base_scale
    bone.append((base_scale.x, base_scale.y, base_scale.z))
    base_rotate = bone_data.base_rotate
    bone.append((base_rotate.v.x, base_rotate.v.y, base_rotate.v.z, base_rotate.s))
    base_translate = bone_data.base_translate
    bone.append((base_translate.x, base_translate.y, base_translate.z))
    bone.append(bone_data.length)

    bones.append(bone)

for vert in skl_data1.data_block.verts:
    verts.append([vert.num_weights, vert.first_weight])

for weight_data in skl_data1.data_block.weights:
    weight = []
    weight.append(weight_data.bone_index)
    weight.append(weight_data.weight_factor)
    op = weight_data.offset_pos
    weight.append((op.x, op.y, op.z))

    weights.append(weight)

for mount_data in skl_data1.data_block.mounts:
    mount = []
    mount.append(mount_data.name)
    mount.append(mount_data.bone_index)
    base_scale = mount_data.base_scale
    mount.append((base_scale.x, base_scale.y, base_scale.z))
    base_rotate = mount_data.base_rotate
    mount.append((base_rotate.v.x, base_rotate.v.y, base_rotate.v.z, base_rotate.s))
    base_translate = mount_data.base_translate
    mount.append((base_translate.x, base_translate.y, base_translate.z))

    mounts.append(mount)

skl_byte_data = create_skl_byte_array(skl_data1.name, bones, verts, weights, mounts)

parse_and_compare_data("SKLB", file_data1["SKLB"][0], skl_byte_data)

# byte_array_list = []
#for key in file_data1:
#    for byte_array in file_data1[key]:
#        byte_array_list.append(byte_array)
#

# Finally write the cpj file to disk
byte_array_list = [ mac_byte_data, geo_byte_data, srf_byte_data, lod_byte_data ]

write_cpj_file("/tmp/out.cpj", byte_array_list)

file_data2 = load_cpj_data("/tmp/out.cpj")

compare_cpj_data(file_data1, file_data2)
