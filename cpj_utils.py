from formats.riff import Riff
import struct

def load_cpj_data(file_path):
    # CPJ files are RIFF compatible files.
    # This means that RIFF readers and writers can load and save CPJ files.
    data = Riff.from_file(file_path)

    # Sanity checks.

    # Is this a RIFF file?
    if not data.is_riff_chunk:
        raise ImportError("This is not a valid CPJ file (The read data is not a RIFF file)")

    # Is this a CPJ file?
    is_cpj = data.parent_chunk_data.form_type == struct.unpack("I", b"CPJB")[0]

    if not is_cpj:
        raise ImportError("Doesn't seem to be a valid cpj file. The header data is incorrect")

    cpj_data = {}

    for sub_chunk in data.subchunks:
        chunk_id_str = sub_chunk.chunk_id_readable

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
