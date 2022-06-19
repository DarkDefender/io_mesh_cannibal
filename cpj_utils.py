import datetime
from formats.riff import Riff
import struct

def load_cpj_data(file_path):
    print("Loading: " + file_path)
    # CPJ files are RIFF compatible files.
    # This means that RIFF readers and writers can load and save CPJ files.
    data = Riff.from_file(file_path)

    # Do two sanity checks.

    # Is this a RIFF file?
    if not data.is_riff_chunk:
        raise ImportError("This is not a valid CPJ file (The read data is not a RIFF file)")

    # Is this a CPJ file?
    is_cpj = data.parent_chunk_data.form_type == struct.unpack("I", b"CPJB")[0]

    if not is_cpj:
        raise ImportError("Doesn't seem to be a valid cpj file. The header form is not of the CPJ type")

    cpj_data = {}

    for sub_chunk in data.subchunks:
        chunk_id_str = sub_chunk.chunk_id_readable
        print(chunk_id_str)

        chunk_data = sub_chunk.chunk_data.data
        # Make sure that the byte array is as if we split this out as a new file
        # Add back the file length
        chunk_data = struct.pack("I", sub_chunk.chunk.len) + chunk_data
        # And the magic id number
        chunk_data = struct.pack("I", sub_chunk.chunk.id) + chunk_data

        if chunk_id_str in cpj_data:
            cpj_data[chunk_id_str].append(chunk_data)
        else:
            cpj_data[chunk_id_str] = [chunk_data]
    return cpj_data

def write_cpj_file(out_file_name, byte_data_list):
    file = open(out_file_name, "wb")

    data_list_byte_len = 0
    # Figure out the total lenght of the packed data
    for byte_array in byte_data_list:
        chunk_len = len(byte_array)
        data_list_byte_len += chunk_len
        # If the length is odd then add a padding byte
        data_list_byte_len += chunk_len % 2

    # Write RIFF magic id
    file.write(b'RIFF')

    # Write total size of all data including the form header (+ 4 bytes)
    file.write(struct.pack("I", data_list_byte_len + 4))

    # Write CPJ form type
    file.write(b'CPJB')

    for byte_array in byte_data_list:
        file.write(byte_array)
        if len(byte_array) % 2 != 0:
            # Add a padding byte (NULL byte)
            file.write(b'\0')
    file.close()

def create_cpj_chunk_header_byte_array(type, data_len, version, name_offset):
    # The header takes up an additonal 3*4 bytes (we start counting total lenght at the version integer)
    data_len += 3*4
    # Create magic type id
    byte_arr = bytes(type, "ASCII")
    # Write the byte lenght of this CPJ chunk
    byte_arr += struct.pack("I", data_len);
    # Write format version
    byte_arr += struct.pack("I", version);
    # Write creation timestamp
    byte_arr += struct.pack("I", int(datetime.datetime.today().timestamp()));
    # Write name offset
    byte_arr += struct.pack("I", name_offset);
    return byte_arr

def string_to_byte_string(str):
    # Return a NULL terminated byte string
    return bytes(str, "ASCII") + b'\x00'

CPJ_FRM_MAGIC = "FRMB"
CPJ_FRM_VERSION = 1
def create_frm_byte_array():
    return

CPJ_GEO_MAGIC = "GEOB"
CPJ_GEO_VERSION = 1
def create_geo_byte_array(name, verts, edges, tris, mounts, obj_links):
    byte_arr = b''
    # The start of the data block (not the chunk).
    data_block_offset = 0

    # Write chunk name (is any)
    if name != "":
        byte_str = string_to_byte_string(name)
        byte_arr += byte_str

        data_block_offset += len(byte_str)

    texture_string_offsets = []

    offset_verts = data_block_offset

    # Write vertex data
    for vert in verts:
        # flags
        byte_arr += struct.pack("B", vert[0]);
        # group_index
        byte_arr += struct.pack("B", vert[1]);
        # reserved
        byte_arr += struct.pack("H", vert[2]);
        # num_edge_links
        byte_arr += struct.pack("H", vert[3]);
        # num_tri_links
        byte_arr += struct.pack("H", vert[4]);
        # first_edge_link
        byte_arr += struct.pack("I", vert[5]);
        # first_tri_link
        byte_arr += struct.pack("I", vert[6]);
        for i in range(3):
            vert_co = vert[7]
            byte_arr += struct.pack("f", vert_co[i]);
        # 2*1 + 3*2 + 2*4 + 3*4
        data_block_offset += 28

    offset_edges = data_block_offset
    # Write edge data
    for edge_data in edges:
        # head_vertex
        byte_arr += struct.pack("H", edge_data[0]);
        # tail_vertex
        byte_arr += struct.pack("H", edge_data[1]);
        # inverted_edge
        byte_arr += struct.pack("H", edge_data[2]);
        # num_tri_links
        byte_arr += struct.pack("H", edge_data[3]);
        # first_tri_link
        byte_arr += struct.pack("I", edge_data[4]);
        # 4*2 + 4 = 22 bytes
        data_block_offset += 12

    offset_tris = data_block_offset
    # Write tri data
    for tri_data in tris:
        # edge ring
        for i in range(3):
            edge_ring = tri_data[0]
            # index of the edge this triangle consists of
            byte_arr += struct.pack("H", edge_ring[i]);
        # reserved
        byte_arr += struct.pack("H", tri_data[1]);
        # 3*2 + 2 = 8 bytes
        data_block_offset += 8

    # Write mount name strings
    mount_str_offsets = []
    for mount_data in mounts:
        byte_str = string_to_byte_string(mount_data[0])
        byte_arr += byte_str

        mount_str_offsets.append(data_block_offset)

        data_block_offset += len(byte_str)

    offset_mounts = data_block_offset
    # Write mount data
    for i in range(len(mounts)):
        mount_data = mount_data[i]
        # offset_name
        byte_arr += struct.pack("I", mount_str_offsets[i]);
        # tri_index
        byte_arr += struct.pack("I", mount_data[1]);
        # tri_barys
        for x in range(3):
            tri_barys = mount_data[2]
            byte_arr += struct.pack("f", tri_barys[x]);
        # base_scale
        for x in range(3):
            base_scale = mount_data[3]
            byte_arr += struct.pack("f", basc_scale[x] );
        # base_rotate
        for x in range(4):
            base_rotate = mount_data[4]
            byte_arr += struct.pack("f", base_rotate[x]);
        # base_translate
        for x in range(3):
            base_translate = mount_data[5]
            byte_arr += struct.pack("f", base_translate[x]);
        # 2*4 + 3*4 + 3*4 + 4*4 + 3*4 = 8 bytes
        data_block_offset += 60

    offset_obj_links = data_block_offset
    # Write object link data
    for obj_link in obj_links:
        # link
        byte_arr += struct.pack("H", obj_link);
        data_block_offset += 2

    geo_info_bytes = b''

    geo_info_bytes += struct.pack("I", len(verts));
    geo_info_bytes += struct.pack("I", offset_verts);

    geo_info_bytes += struct.pack("I", len(edges));
    geo_info_bytes += struct.pack("I", offset_edges);

    geo_info_bytes += struct.pack("I", len(tris));
    geo_info_bytes += struct.pack("I", offset_tris);

    geo_info_bytes += struct.pack("I", len(mounts));
    geo_info_bytes += struct.pack("I", offset_mounts);

    geo_info_bytes += struct.pack("I", len(obj_links));
    geo_info_bytes += struct.pack("I", offset_obj_links);

    info_offset = 10*4
    # The cpj header is 20 bytes (5*4)
    name_offset = 20 + info_offset

    # We already took into account the offset of these info variables at the start of the function
    data_len = data_block_offset + info_offset

    geo_header_byte_arr = create_cpj_chunk_header_byte_array(CPJ_GEO_MAGIC, data_len, CPJ_GEO_VERSION, name_offset)
    byte_arr = geo_header_byte_arr + geo_info_bytes + byte_arr

    # Sanity check
    if (len(byte_arr) != data_len + 20):
        raise ValueError("The calculated byte lenght of the array doesn't match up with the actual size!")

    return byte_arr

CPJ_LOD_MAGIC = "LODB"
CPJ_LOD_VERSION = 3
def create_lod_byte_array():
    return

CPJ_MAC_MAGIC = "MACB"
CPJ_MAC_VERSION = 1
def create_mac_byte_array(name, command_strings):
    byte_arr = b''
    # The start of the data block (not the chunk).
    data_block_offset = 0

    # Write chunk name (if any)
    if name != "":
        byte_str = string_to_byte_string(name)
        byte_arr += byte_str

        data_block_offset += len(byte_str)

    # Write section data
    # TODO for now we always assume that there is one section and that it is always "autoexec"
    section_names = ["autoexec"]
    num_sections = 1
    sec_num_commands = len(command_strings)
    first_sec_command = 0
    sec_offset_names = []

    # Write all section name strings in a contious block
    for sec_name in section_names:
        sec_offset_names.append(data_block_offset)
        byte_str = string_to_byte_string(sec_name)
        byte_arr += byte_str

        data_block_offset += len(byte_str)

    offset_sections = data_block_offset
    # Write all section data in a contious block
    for i in range(num_sections):
        # TODO currently this is only written to handle the dummy autoexec case
        byte_arr += struct.pack("I", sec_offset_names[i]);
        byte_arr += struct.pack("I", sec_num_commands);
        byte_arr += struct.pack("I", first_sec_command);

        data_block_offset += 12 #(3 * 4) bytes for each section

    com_str_offsets = []

    # Write command strings in a contious block
    for command in command_strings:
        com_str_offsets.append(data_block_offset)
        byte_str = string_to_byte_string(command)
        byte_arr += byte_str

        data_block_offset += len(byte_str)

    offset_commands = data_block_offset

    # Write command data in a contious block
    for offset in com_str_offsets:
        byte_arr += struct.pack("I", offset);

        data_block_offset += 4

    mac_info_bytes = b''

    mac_info_bytes += struct.pack("I", num_sections);
    mac_info_bytes += struct.pack("I", offset_sections);

    mac_info_bytes += struct.pack("I", len(command_strings));
    mac_info_bytes += struct.pack("I", offset_commands);

    info_offset = 4*4
    # The cpj header is 20 bytes (5*4)
    name_offset = 20 + info_offset

    # We already took into account the offset of these info variables at the start of the function
    data_len = data_block_offset + info_offset

    mac_header_byte_arr = create_cpj_chunk_header_byte_array(CPJ_MAC_MAGIC, data_len, CPJ_MAC_VERSION, name_offset)
    # Add it all together
    byte_arr = mac_header_byte_arr + mac_info_bytes + byte_arr

    # Sanity check
    if (len(byte_arr) != data_len + 20):
        raise ValueError("The calculated byte lenght of the array doesn't match up with the actual size!")

    return byte_arr

CPJ_SEQ_MAGIC = "SEQB"
CPJ_SEQ_VERSION = 1
def create_seq_byte_array():
    return

CPJ_SKL_MAGIC = "SKLB"
CPJ_SKL_VERSION = 1
def create_skl_byte_array():
    return

CPJ_SRF_MAGIC = "SRFB"
CPJ_SRF_VERSION = 1
def create_srf_byte_array(name, textures, tris, uv_coords):
    byte_arr = b''
    # The start of the data block (not the chunk).
    data_block_offset = 0

    # Write chunk name (is any)
    if name != "":
        byte_str = string_to_byte_string(name)
        byte_arr += byte_str

        data_block_offset += len(byte_str)

    texture_string_offsets = []

    # Write texture data strings
    for texture_data in textures:
        offsets = [0,0]
        offsets[0] = data_block_offset
        byte_str = string_to_byte_string(texture_data[0])
        byte_arr += byte_str
        data_block_offset += len(byte_str)

        if texture_data[1] != "":
            offsets[1] = data_block_offset
            byte_str = string_to_byte_string(texture_data[1])
            byte_arr += byte_str
            data_block_offset += len(byte_str)
        texture_string_offsets.append(offsets)

    offset_textures = data_block_offset

    # Write texture string offsets
    for offsets in texture_string_offsets:
        byte_arr += struct.pack("I", offsets[0]);
        byte_arr += struct.pack("I", offsets[1]);
        data_block_offset += 8 #(2 * 4) bytes for each section

    offset_tris = data_block_offset
    # Write triangle data
    for tri_data in tris:
        # uv_index
        for i in range(3):
            uv_index = tri_data[0]
            # index of uvs in uv_coords
            byte_arr += struct.pack("H", uv_index[i]);
        # tex_index
        byte_arr += struct.pack("B", tri_data[1]);
        # reserved
        byte_arr += struct.pack("B", tri_data[2]);
        # flags
        byte_arr += struct.pack("I", tri_data[3]);
        # smooth_group
        byte_arr += struct.pack("B", tri_data[4]);
        # alpha_level
        byte_arr += struct.pack("B", tri_data[5]);
        # glaze_tex_index
        byte_arr += struct.pack("B", tri_data[6]);
        # glaze_func
        byte_arr += struct.pack("B", tri_data[7]);
        # 3*2 + 2*1 + 4 + 4*1 = 16 bytes
        data_block_offset += 16

    offset_uvs = data_block_offset
    for uv_co in uv_coords:
        byte_arr += struct.pack("f", uv_co[0]);
        byte_arr += struct.pack("f", uv_co[1]);
        data_block_offset += 8 #(2 * 4) bytes for each section

    srf_info_bytes = b''

    srf_info_bytes += struct.pack("I", len(textures));
    srf_info_bytes += struct.pack("I", offset_textures);

    srf_info_bytes += struct.pack("I", len(tris));
    srf_info_bytes += struct.pack("I", offset_tris);

    srf_info_bytes += struct.pack("I", len(uv_coords));
    srf_info_bytes += struct.pack("I", offset_uvs);

    info_offset = 6*4
    # The cpj header is 20 bytes (5*4)
    name_offset = 20 + info_offset

    # We already took into account the offset of these info variables at the start of the function
    data_len = data_block_offset + info_offset

    srf_header_byte_arr = create_cpj_chunk_header_byte_array(CPJ_SRF_MAGIC, data_len, CPJ_SRF_VERSION, name_offset)
    byte_arr = srf_header_byte_arr + srf_info_bytes + byte_arr

    # Sanity check
    if (len(byte_arr) != data_len + 20):
        raise ValueError("The calculated byte lenght of the array doesn't match up with the actual size!")

    return byte_arr
