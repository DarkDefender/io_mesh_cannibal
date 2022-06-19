# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Frm(KaitaiStruct):
    """A vertex frames chunk holds one or more vertex frames.  Each vertex frame
    can be applied directly to the vertices of a geometry definition, for
    frame-based animation.  The positions may either be raw uncompressed vectors,
    or compressed into byte positions according to the vertex group indices.
    
    .. seealso::
       Cannibal/CpjFmt.h
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.cpj_chunk_header = Frm.CpjChunkHeader(self._io, self, self._root)
        self.bb_min = Frm.Vec3f(self._io, self, self._root)
        self.bb_max = Frm.Vec3f(self._io, self, self._root)
        self.num_frames = self._io.read_u4le()
        self.data_offset_frames = self._io.read_u4le()
        self._raw_data_block = self._io.read_bytes_full()
        _io__raw_data_block = KaitaiStream(BytesIO(self._raw_data_block))
        self.data_block = Frm.DataBlock(_io__raw_data_block, self, self._root)

    class Frame(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_name = self._io.read_u4le()
            self.bb_min = Frm.Vec3f(self._io, self, self._root)
            self.bb_max = Frm.Vec3f(self._io, self, self._root)
            self.num_groups = self._io.read_u4le()
            self.data_offset_groups = self._io.read_u4le()
            self.num_verts = self._io.read_u4le()
            self.data_offset_verts = self._io.read_u4le()

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
        def groups(self):
            if hasattr(self, '_m_groups'):
                return self._m_groups if hasattr(self, '_m_groups') else None

            if self.num_groups != 0:
                _pos = self._io.pos()
                self._io.seek(self.data_offset_groups)
                self._m_groups = [None] * (self.num_groups)
                for i in range(self.num_groups):
                    self._m_groups[i] = Frm.Group(self._io, self, self._root)

                self._io.seek(_pos)

            return self._m_groups if hasattr(self, '_m_groups') else None

        @property
        def verts(self):
            if hasattr(self, '_m_verts'):
                return self._m_verts if hasattr(self, '_m_verts') else None

            _pos = self._io.pos()
            self._io.seek(self.data_offset_verts)
            self._m_verts = [None] * (self.num_verts)
            for i in range(self.num_verts):
                _on = self.num_groups
                if _on == 0:
                    self._m_verts[i] = Frm.Vec3f(self._io, self, self._root)
                else:
                    self._m_verts[i] = Frm.BytePos(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_verts if hasattr(self, '_m_verts') else None


    class CpjChunkHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x46\x52\x4D\x42":
                raise kaitaistruct.ValidationNotEqualError(b"\x46\x52\x4D\x42", self.magic, self._io, u"/types/cpj_chunk_header/seq/0")
            self.file_len = self._io.read_u4le()
            self.version = self._io.read_u4le()
            self.time_stamp = self._io.read_u4le()
            self.offset_name = self._io.read_u4le()


    class BytePos(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.group = self._io.read_u1()
            self.pos = [None] * (3)
            for i in range(3):
                self.pos[i] = self._io.read_u1()



    class DataBlock(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass

        @property
        def frames(self):
            if hasattr(self, '_m_frames'):
                return self._m_frames if hasattr(self, '_m_frames') else None

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_frames)
            self._m_frames = [None] * (self._root.num_frames)
            for i in range(self._root.num_frames):
                self._m_frames[i] = Frm.Frame(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_frames if hasattr(self, '_m_frames') else None


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


    class Group(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.byte_scale = Frm.Vec3f(self._io, self, self._root)
            self.byte_translate = Frm.Vec3f(self._io, self, self._root)


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


