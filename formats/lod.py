# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Lod(KaitaiStruct):
    """These chunks store level of detail reduction information based on a specific
    combination of a geometry chunk and surface chunk.  The information describes
    discrete levels of detail in the form of alternate geometry and primary
    surface information to use at lower levels of detail, the level being one
    at full detail and zero at lowest detail (maximum distance).  Each level
    contains a vertex relay to the original geometry vertex indices, so that the
    lower details can use the same frame and sequence chunks as the original.
    The relay is a list of vertex index values into the original geometry, and
    its count indicates the number of vertices used by the level.  The triangle
    vertex indices are not actual geometry indices, but indices into the relay.
    UV indices directly map to the UVs of the original surface.
    
    Note that this form of LOD storage is not entirely compact, and is does not
    permit full (continuous) level of detail reduction.  This is a deliberate
    tradeoff of memory efficiency and flexibility in exchange for raw runtime
    speed.
    
    .. seealso::
       Cannibal/CpjFmt.h
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.cpj_chunk_header = Lod.CpjChunkHeader(self._io, self, self._root)
        self.num_levels = self._io.read_u4le()
        self.data_offset_levels = self._io.read_u4le()
        self.num_tris = self._io.read_u4le()
        self.data_offset_tris = self._io.read_u4le()
        self.num_vert_relay = self._io.read_u4le()
        self.data_offset_vert_relay = self._io.read_u4le()
        self._raw_data_block = self._io.read_bytes_full()
        _io__raw_data_block = KaitaiStream(BytesIO(self._raw_data_block))
        self.data_block = Lod.DataBlock(_io__raw_data_block, self, self._root)

    class CpjChunkHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x4C\x4F\x44\x42":
                raise kaitaistruct.ValidationNotEqualError(b"\x4C\x4F\x44\x42", self.magic, self._io, u"/types/cpj_chunk_header/seq/0")
            self.file_len = self._io.read_u4le()
            self.version = self._io.read_u4le()
            self.time_stamp = self._io.read_u4le()
            self.offset_name = self._io.read_u4le()


    class DataBlock(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def levels(self):
            if hasattr(self, '_m_levels'):
                return self._m_levels

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_levels)
            self._m_levels = []
            for i in range(self._root.num_levels):
                self._m_levels.append(Lod.Level(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_levels', None)

        @property
        def tris(self):
            if hasattr(self, '_m_tris'):
                return self._m_tris

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_tris)
            self._m_tris = []
            for i in range(self._root.num_tris):
                self._m_tris.append(Lod.Tri(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_tris', None)

        @property
        def vert_relay(self):
            if hasattr(self, '_m_vert_relay'):
                return self._m_vert_relay

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_vert_relay)
            self._m_vert_relay = []
            for i in range(self._root.num_vert_relay):
                self._m_vert_relay.append(self._io.read_u2le())

            self._io.seek(_pos)
            return getattr(self, '_m_vert_relay', None)


    class Level(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.detail = self._io.read_f4le()
            self.num_tri = self._io.read_u4le()
            self.num_vert_relay = self._io.read_u4le()
            self.first_tri = self._io.read_u4le()
            self.first_vert_relay = self._io.read_u4le()


    class Tri(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.tri_index = self._io.read_u4le()
            self.vert_index = []
            for i in range(3):
                self.vert_index.append(self._io.read_u2le())

            self.uv_index = []
            for i in range(3):
                self.uv_index.append(self._io.read_u2le())



    @property
    def name(self):
        if hasattr(self, '_m_name'):
            return self._m_name

        if self.cpj_chunk_header.offset_name != 0:
            _pos = self._io.pos()
            self._io.seek(self.cpj_chunk_header.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)

        return getattr(self, '_m_name', None)


