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

def create_frm_byte_array():
    return

def create_geo_byte_array():
    return

def create_lod_byte_array():
    return

def create_mac_byte_array():
    return

def create_seq_byte_array():
    return

def create_skl_byte_array():
    return

def create_srf_byte_array():
    return
