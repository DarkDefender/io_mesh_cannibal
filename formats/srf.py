# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Srf(KaitaiStruct):
    """The surface chunk of a model describes the surface properties of its
    triangles for rendering and so forth.  It contains texture map coordinates,
    texture names used by the triangles, various display-related flags, and other
    supplemental information.  The number of triangles used should match the
    number of triangles in the geometry chunk.  Surfaces can be stacked together
    on top of a model, with the first surface acting as the primary "skin" of
    the model and additional surfaces being used for decals (where non-decaled
    triangles are flagged as inactive).
    
    .. seealso::
       Cannibal/CpjFmt.h
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.cpj_chunk_header = Srf.CpjChunkHeader(self._io, self, self._root)
        self.num_textures = self._io.read_u4le()
        self.data_offset_textures = self._io.read_u4le()
        self.num_tris = self._io.read_u4le()
        self.data_offset_tris = self._io.read_u4le()
        self.num_uv = self._io.read_u4le()
        self.data_offset_uv = self._io.read_u4le()
        self._raw_data_block = self._io.read_bytes_full()
        _io__raw_data_block = KaitaiStream(BytesIO(self._raw_data_block))
        self.data_block = Srf.DataBlock(_io__raw_data_block, self, self._root)

    class Uv(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.u = self._io.read_f4le()
            self.v = self._io.read_f4le()


    class Tri(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.uv_index = []
            for i in range(3):
                self.uv_index.append(self._io.read_u2le())

            self.tex_index = self._io.read_u1()
            self.reserved = self._io.read_u1()
            self.flags = self._io.read_u4le()
            self.smooth_group = self._io.read_u1()
            self.alpha_level = self._io.read_u1()
            self.glaze_tex_index = self._io.read_u1()
            self.glaze_func = self._io.read_u1()


    class CpjChunkHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x53\x52\x46\x42":
                raise kaitaistruct.ValidationNotEqualError(b"\x53\x52\x46\x42", self.magic, self._io, u"/types/cpj_chunk_header/seq/0")
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
        def textures(self):
            if hasattr(self, '_m_textures'):
                return self._m_textures

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_textures)
            self._m_textures = []
            for i in range(self._root.num_textures):
                self._m_textures.append(Srf.Texture(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_textures', None)

        @property
        def tris(self):
            if hasattr(self, '_m_tris'):
                return self._m_tris

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_tris)
            self._m_tris = []
            for i in range(self._root.num_tris):
                self._m_tris.append(Srf.Tri(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_tris', None)

        @property
        def uvs(self):
            if hasattr(self, '_m_uvs'):
                return self._m_uvs

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_uv)
            self._m_uvs = []
            for i in range(self._root.num_uv):
                self._m_uvs.append(Srf.Uv(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_uvs', None)


    class Texture(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_name = self._io.read_u4le()
            self.offset_ref_name = self._io.read_u4le()

        @property
        def name(self):
            if hasattr(self, '_m_name'):
                return self._m_name

            _pos = self._io.pos()
            self._io.seek(self.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)
            return getattr(self, '_m_name', None)

        @property
        def ref_name(self):
            if hasattr(self, '_m_ref_name'):
                return self._m_ref_name

            if self.offset_ref_name != 0:
                _pos = self._io.pos()
                self._io.seek(self.offset_ref_name)
                self._m_ref_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
                self._io.seek(_pos)

            return getattr(self, '_m_ref_name', None)


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


