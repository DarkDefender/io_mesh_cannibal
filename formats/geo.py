# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Geo(KaitaiStruct):
    """These chunks contain a description of a model's triangular mesh geometry
    boundary representation which is unchanged regardless of a model instance's
    animation state.  It describes vertices, edges, triangles, and the
    connections between them, as well any mount points associated with the
    model geometry.
    
    .. seealso::
       Cannibal/CpjFmt.h
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.cpj_chunk_header = Geo.CpjChunkHeader(self._io, self, self._root)
        self.num_verts = self._io.read_u4le()
        self.data_offset_verts = self._io.read_u4le()
        self.num_edges = self._io.read_u4le()
        self.data_offset_edges = self._io.read_u4le()
        self.num_tris = self._io.read_u4le()
        self.data_offset_tris = self._io.read_u4le()
        self.num_mounts = self._io.read_u4le()
        self.data_offset_mounts = self._io.read_u4le()
        self.num_obj_links = self._io.read_u4le()
        self.data_offset_obj_links = self._io.read_u4le()
        self._raw_data_block = self._io.read_bytes_full()
        _io__raw_data_block = KaitaiStream(BytesIO(self._raw_data_block))
        self.data_block = Geo.DataBlock(_io__raw_data_block, self, self._root)

    class Vert(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.flags = self._io.read_u1()
            self.group_index = self._io.read_u1()
            self.reserved = self._io.read_u2le()
            self.num_edge_links = self._io.read_u2le()
            self.num_tri_links = self._io.read_u2le()
            self.first_edge_link = self._io.read_u4le()
            self.first_tri_link = self._io.read_u4le()
            self.ref_pos = Geo.Vec3f(self._io, self, self._root)


    class Tri(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.edge_ring = []
            for i in range(3):
                self.edge_ring.append(self._io.read_u2le())

            self.reserved = self._io.read_u2le()


    class CpjChunkHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x47\x45\x4F\x42":
                raise kaitaistruct.ValidationNotEqualError(b"\x47\x45\x4F\x42", self.magic, self._io, u"/types/cpj_chunk_header/seq/0")
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
            self.v = Geo.Vec3f(self._io, self, self._root)
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
        def triangles(self):
            if hasattr(self, '_m_triangles'):
                return self._m_triangles

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_tris)
            self._m_triangles = []
            for i in range(self._root.num_tris):
                self._m_triangles.append(Geo.Tri(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_triangles', None)

        @property
        def obj_links(self):
            if hasattr(self, '_m_obj_links'):
                return self._m_obj_links

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_obj_links)
            self._m_obj_links = []
            for i in range(self._root.num_obj_links):
                self._m_obj_links.append(Geo.ObjLink(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_obj_links', None)

        @property
        def vertices(self):
            if hasattr(self, '_m_vertices'):
                return self._m_vertices

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_verts)
            self._m_vertices = []
            for i in range(self._root.num_verts):
                self._m_vertices.append(Geo.Vert(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_vertices', None)

        @property
        def mounts(self):
            if hasattr(self, '_m_mounts'):
                return self._m_mounts

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_mounts)
            self._m_mounts = []
            for i in range(self._root.num_mounts):
                self._m_mounts.append(Geo.Mount(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_mounts', None)

        @property
        def edges(self):
            if hasattr(self, '_m_edges'):
                return self._m_edges

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_edges)
            self._m_edges = []
            for i in range(self._root.num_edges):
                self._m_edges.append(Geo.Edge(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_edges', None)


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


    class Edge(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.head_vertex = self._io.read_u2le()
            self.tail_vertex = self._io.read_u2le()
            self.inverted_edge = self._io.read_u2le()
            self.num_tri_links = self._io.read_u2le()
            self.first_tri_link = self._io.read_u4le()


    class Mount(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_name = self._io.read_u4le()
            self.tri_index = self._io.read_u4le()
            self.tri_barys = Geo.Vec3f(self._io, self, self._root)
            self.base_scale = Geo.Vec3f(self._io, self, self._root)
            self.base_rotate = Geo.Quat(self._io, self, self._root)
            self.base_translate = Geo.Vec3f(self._io, self, self._root)

        @property
        def name(self):
            if hasattr(self, '_m_name'):
                return self._m_name

            _pos = self._io.pos()
            self._io.seek(self.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)
            return getattr(self, '_m_name', None)


    class ObjLink(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.link = self._io.read_u2le()


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


