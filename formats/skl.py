# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Skl(KaitaiStruct):
    """These chunks, if present, allow a model to be capable of skeletal-based
    animation.  It contains a list of bones with their initial transforms and
    hierarchical parents, as well as the vertex weights to use when applying a
    matching geometry chunk.  All bone transforms are relative to their parents,
    and the indices of the vertices should correspond to the vertices of the
    geometry chunk being used.  These chunks also hold any mount points
    associated with the skeleton.
    
    .. seealso::
       Cannibal/CpjFmt.h
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.cpj_chunk_header = Skl.CpjChunkHeader(self._io, self, self._root)
        self.num_bones = self._io.read_u4le()
        self.data_offset_bones = self._io.read_u4le()
        self.num_verts = self._io.read_u4le()
        self.data_offset_verts = self._io.read_u4le()
        self.num_weights = self._io.read_u4le()
        self.data_offset_weights = self._io.read_u4le()
        self.num_mounts = self._io.read_u4le()
        self.data_offset_mounts = self._io.read_u4le()
        self._raw_data_block = self._io.read_bytes_full()
        _io__raw_data_block = KaitaiStream(BytesIO(self._raw_data_block))
        self.data_block = Skl.DataBlock(_io__raw_data_block, self, self._root)

    class Weight(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.bone_index = self._io.read_u4le()
            self.weight_factor = self._io.read_f4le()
            self.offset_pos = Skl.Vec3f(self._io, self, self._root)


    class Vert(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.num_weights = self._io.read_u2le()
            self.first_weight = self._io.read_u2le()


    class Bone(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_name = self._io.read_u4le()
            self.parent_index = self._io.read_u4le()
            self.base_scale = Skl.Vec3f(self._io, self, self._root)
            self.base_rotate = Skl.Quat(self._io, self, self._root)
            self.base_translate = Skl.Vec3f(self._io, self, self._root)
            self.length = self._io.read_f4le()

        @property
        def name(self):
            if hasattr(self, '_m_name'):
                return self._m_name if hasattr(self, '_m_name') else None

            _pos = self._io.pos()
            self._io.seek(self.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)
            return self._m_name if hasattr(self, '_m_name') else None


    class CpjChunkHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x53\x4B\x4C\x42":
                raise kaitaistruct.ValidationNotEqualError(b"\x53\x4B\x4C\x42", self.magic, self._io, u"/types/cpj_chunk_header/seq/0")
            self.file_len = self._io.read_u4le()
            self.version = self._io.read_u4le()
            self.time_stamp = self._io.read_u4le()
            self.offset_name = self._io.read_u4le()


    class Quat(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.v = Skl.Vec3f(self._io, self, self._root)
            self.s = self._io.read_f4le()


    class DataBlock(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def bones(self):
            if hasattr(self, '_m_bones'):
                return self._m_bones if hasattr(self, '_m_bones') else None

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_bones)
            self._m_bones = [None] * (self._root.num_bones)
            for i in range(self._root.num_bones):
                self._m_bones[i] = Skl.Bone(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_bones if hasattr(self, '_m_bones') else None

        @property
        def verts(self):
            if hasattr(self, '_m_verts'):
                return self._m_verts if hasattr(self, '_m_verts') else None

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_verts)
            self._m_verts = [None] * (self._root.num_verts)
            for i in range(self._root.num_verts):
                self._m_verts[i] = Skl.Vert(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_verts if hasattr(self, '_m_verts') else None

        @property
        def weights(self):
            if hasattr(self, '_m_weights'):
                return self._m_weights if hasattr(self, '_m_weights') else None

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_weights)
            self._m_weights = [None] * (self._root.num_weights)
            for i in range(self._root.num_weights):
                self._m_weights[i] = Skl.Weight(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_weights if hasattr(self, '_m_weights') else None

        @property
        def mounts(self):
            if hasattr(self, '_m_mounts'):
                return self._m_mounts if hasattr(self, '_m_mounts') else None

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_mounts)
            self._m_mounts = [None] * (self._root.num_mounts)
            for i in range(self._root.num_mounts):
                self._m_mounts[i] = Skl.Mount(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_mounts if hasattr(self, '_m_mounts') else None


    class Vec3f(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.x = self._io.read_f4le()
            self.y = self._io.read_f4le()
            self.z = self._io.read_f4le()


    class Mount(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_name = self._io.read_u4le()
            self.bone_index = self._io.read_u4le()
            self.base_scale = Skl.Vec3f(self._io, self, self._root)
            self.base_rotate = Skl.Quat(self._io, self, self._root)
            self.base_translate = Skl.Vec3f(self._io, self, self._root)

        @property
        def name(self):
            if hasattr(self, '_m_name'):
                return self._m_name if hasattr(self, '_m_name') else None

            _pos = self._io.pos()
            self._io.seek(self.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)
            return self._m_name if hasattr(self, '_m_name') else None


    @property
    def name(self):
        if hasattr(self, '_m_name'):
            return self._m_name if hasattr(self, '_m_name') else None

        if self.cpj_chunk_header.offset_name != 0:
            _pos = self._io.pos()
            self._io.seek(self.cpj_chunk_header.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)

        return self._m_name if hasattr(self, '_m_name') else None


