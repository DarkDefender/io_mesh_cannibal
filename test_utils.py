from cpj_utils import *

def round_trip_frm_data(frm_data):
    # construct a vertex frame animation data list from parsed data
    frames = []
    for frame_data in frm_data.data_block.frames:
        frame = []
        frame.append(frame_data.name)
        bb_min = frame_data.bb_min
        frame.append((bb_min.x, bb_min.y, bb_min.z))
        bb_max = frame_data.bb_max
        frame.append((bb_max.x, bb_max.y, bb_max.z))

        frame.append(frame_data.num_groups)
        frame_groups = []
        for group_data in frame_data.groups:
            byte_scale = group_data.byte_scale
            bs = (byte_scale.x, byte_scale.y, byte_scale.z)
            byte_trans = group_data.byte_translate
            bt = (byte_trans.x, byte_trans.y, byte_trans.z)
            frame_groups.append((bs, bt))
        frame.append(frame_groups)

        frame.append(frame_data.num_verts)
        frame_verts = []
        for vert_data in frame_data.verts:
            if (frame_data.num_groups == 0):
                # Save uncompressed vert data
                frame_verts.append((vert_data.x, vert_data.y, vert_data.z))
                continue
            # Save compressed data
            pos = vert_data.pos
            frame_verts.append((vert_data.group, (pos[0], pos[1], pos[2])))
        frame.append(frame_verts)

        frames.append(frame)

    frm_bb_min = (frm_data.bb_min.x, frm_data.bb_min.y, frm_data.bb_min.z)
    frm_bb_max = (frm_data.bb_max.x, frm_data.bb_max.y, frm_data.bb_max.z)

    frm_byte_data = create_frm_byte_array(frm_data.name, (frm_bb_min, frm_bb_max), frames)

    return frm_byte_data

def round_trip_geo_data(geo_data):
    # construct geo data lists
    verts = []
    edges = []
    tris = []
    mounts = []
    obj_links = []

    for vert_data in geo_data.data_block.vertices:
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

    for edge_data in geo_data.data_block.edges:
        edge = []
        edge.append(edge_data.head_vertex)
        edge.append(edge_data.tail_vertex)
        edge.append(edge_data.inverted_edge)
        edge.append(edge_data.num_tri_links)
        edge.append(edge_data.first_tri_link)

        edges.append(edge)

    for tri_data in geo_data.data_block.triangles:
        tri = []
        edge_ring = tri_data.edge_ring
        tri.append((edge_ring[0], edge_ring[1], edge_ring[2]))
        tri.append(tri_data.reserved)

        tris.append(tri)

    for mount_data in geo_data.data_block.mounts:
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

    for obj_link_data in geo_data.data_block.obj_links:
        obj_links.append(obj_link_data.link)

    geo_byte_data = create_geo_byte_array(geo_data.name, verts, edges, tris, mounts, obj_links)

    return geo_byte_data

def round_trip_lod_data(lod_data):
    # construct lod data lists
    levels = []
    tris = []
    vert_relay = []

    for level_data in lod_data.data_block.levels:
        level = []
        level.append(level_data.detail)
        level.append(level_data.num_tri)
        level.append(level_data.num_vert_relay)
        level.append(level_data.first_tri)
        level.append(level_data.first_vert_relay)

        levels.append(level)

    for tris_data in lod_data.data_block.tris:
        tri = []
        tri.append(tris_data.tri_index)
        vert_idx = tris_data.vert_index
        tri.append((vert_idx[0], vert_idx[1], vert_idx[2]))
        uv_idx = tris_data.uv_index
        tri.append((uv_idx[0], uv_idx[1], uv_idx[2]))

        tris.append(tri)

    for vert_relay_data in lod_data.data_block.vert_relay:
        vert_relay.append(vert_relay_data)

    lod_byte_data = create_lod_byte_array(lod_data.name, levels, tris, vert_relay)

    return lod_byte_data

def round_trip_mac_data(mac_data):
    # construct a mac information data list
    section_data = []
    command_strings = []
    for sec in mac_data.data_block.sections:
        sec_data = []
        sec_data.append(sec.name)
        sec_data.append(sec.num_commands)
        sec_data.append(sec.first_command)

        section_data.append(sec_data)

    for com in mac_data.data_block.commands:
        command_strings.append(com.command_str)

    mac_byte_data = create_mac_byte_array(mac_data.name, section_data, command_strings)

    return mac_byte_data

def round_trip_seq_data(seq_data):
    # construct a seq data list
    frames = []
    events = []
    bone_info = []
    bone_translate = []
    bone_rotate = []
    bone_scale = []

    for frame_data in seq_data.data_block.frames:
        frame = []
        frame.append(frame_data.reserved)
        frame.append(frame_data.num_bone_translate)
        frame.append(frame_data.num_bone_rotate)
        frame.append(frame_data.num_bone_scale)
        frame.append(frame_data.first_bone_translate)
        frame.append(frame_data.first_bone_rotate)
        frame.append(frame_data.first_bone_scale)
        frame.append(frame_data.vert_frame_name)

        frames.append(frame)

    for event_data in seq_data.data_block.events:
        event = []
        event.append(event_data.event_type)
        event.append(event_data.time)
        event.append(event_data.param_str)

        events.append(event)

    for bone_i_data in seq_data.data_block.bone_info:
        bone_i = []
        bone_i.append(bone_i_data.name)
        bone_i.append(bone_i_data.src_length)

        bone_info.append(bone_i)

    for bone_t_data in seq_data.data_block.bone_translate:
        bone_t = []
        bone_t.append(bone_t_data.bone_index)
        bone_t.append(bone_t_data.reserved)
        trans = bone_t_data.translate
        bone_t.append((trans.x, trans.y, trans.z))

        bone_translate.append(bone_t)

    for bone_r_data in seq_data.data_block.bone_rotate:
        bone_r = []
        bone_r.append(bone_r_data.bone_index)
        bone_r.append(bone_r_data.roll)
        bone_r.append(bone_r_data.pitch)
        bone_r.append(bone_r_data.yaw)

        bone_rotate.append(bone_r)

    for bone_s_data in seq_data.data_block.bone_scale:
        bone_s = []
        bone_s.append(bone_s_data.bone_index)
        bone_s.append(bone_s_data.reserved)
        scale = bone_s_data.scale
        bone_s.append((scale.x, scale.y, scale.z))

        bone_scale.append(bone_s)

    seq_byte_data = create_seq_byte_array(seq_data.name, seq_data.play_rate, frames, events, bone_info, bone_translate, bone_rotate, bone_scale)

    return seq_byte_data

def round_trip_skl_data(skl_data):
    # construct a skl data lists
    bones = []
    verts = []
    weights = []
    mounts = []

    for bone_data in skl_data.data_block.bones:
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

    for vert in skl_data.data_block.verts:
        verts.append([vert.num_weights, vert.first_weight])

    for weight_data in skl_data.data_block.weights:
        weight = []
        weight.append(weight_data.bone_index)
        weight.append(weight_data.weight_factor)
        op = weight_data.offset_pos
        weight.append((op.x, op.y, op.z))

        weights.append(weight)

    for mount_data in skl_data.data_block.mounts:
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

    skl_byte_data = create_skl_byte_array(skl_data.name, bones, verts, weights, mounts)

    return skl_byte_data

def round_trip_srf_data(srf_data):
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
