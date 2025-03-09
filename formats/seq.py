# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Seq(KaitaiStruct):
    """A sequenced animation chunk contains an animation sequence in the form frame
    structures which hold the state of the animation at a given point in the
    sequence, containing skeletal and/or frame-based animation information.
    The sequence can be executed in one of a model instance's runtime animation
    "channels" at a given frames per second playback rate, and can be combined
    with other channels to produce composite animations.  In addition, the
    sequence may contain a series of "events" to fire at a particular point
    during playback.
    
    Since sequenced animation data is independent of any particular project,
    all model resources needed are referred to by name, which can be bound to
    actual model resources at runtime.  Each frame may refer to a single vertex
    frame for frame-based animations, and/or a collection of bones for skeletal
    animation.  Most skeletal animations will only use the rotate component, and
    as such it is compressed into 16-bit euler angles.  The translate and scale
    components are still supported, but are less common and left at full
    precision.  All skeletal transformations are relative to the initial
    structure transformation of the corresponding bone (which is then relative
    to the bone's parent), to allow the animation to be used by multiple skeleton
    structures.  During playback, the usage of any bones that are not described
    by the sequence is determined by the implementation.  The bones may be left
    in their default state, or ignored entirely, depending on context.
    
    .. seealso::
       Cannibal/CpjFmt.h
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.cpj_chunk_header = Seq.CpjChunkHeader(self._io, self, self._root)
        self.play_rate = self._io.read_f4le()
        self.num_frames = self._io.read_u4le()
        self.data_offset_frames = self._io.read_u4le()
        self.num_events = self._io.read_u4le()
        self.data_offset_events = self._io.read_u4le()
        self.num_bone_info = self._io.read_u4le()
        self.data_offset_bone_info = self._io.read_u4le()
        self.num_bone_translate = self._io.read_u4le()
        self.data_offset_bone_translate = self._io.read_u4le()
        self.num_bone_rotate = self._io.read_u4le()
        self.data_offset_bone_rotate = self._io.read_u4le()
        self.num_bone_scale = self._io.read_u4le()
        self.data_offset_bone_scale = self._io.read_u4le()
        self._raw_data_block = self._io.read_bytes_full()
        _io__raw_data_block = KaitaiStream(BytesIO(self._raw_data_block))
        self.data_block = Seq.DataBlock(_io__raw_data_block, self, self._root)

    class BoneInfo(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_name = self._io.read_u4le()
            self.src_length = self._io.read_f4le()

        @property
        def name(self):
            if hasattr(self, '_m_name'):
                return self._m_name

            _pos = self._io.pos()
            self._io.seek(self.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)
            return getattr(self, '_m_name', None)


    class Event(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.event_type = (self._io.read_bytes(4)).decode(u"ASCII")
            self.time = self._io.read_f4le()
            self.offset_param_str = self._io.read_s4le()

        @property
        def param_str(self):
            if hasattr(self, '_m_param_str'):
                return self._m_param_str

            if self.offset_param_str != -1:
                _pos = self._io.pos()
                self._io.seek(self.offset_param_str)
                self._m_param_str = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
                self._io.seek(_pos)

            return getattr(self, '_m_param_str', None)


    class BoneRotate(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.bone_index = self._io.read_u2le()
            self.roll = self._io.read_s2le()
            self.pitch = self._io.read_s2le()
            self.yaw = self._io.read_s2le()


    class Frame(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.reserved = self._io.read_u1()
            self.num_bone_translate = self._io.read_u1()
            self.num_bone_rotate = self._io.read_u1()
            self.num_bone_scale = self._io.read_u1()
            self.first_bone_translate = self._io.read_u4le()
            self.first_bone_rotate = self._io.read_u4le()
            self.first_bone_scale = self._io.read_u4le()
            self.offset_vert_frame_name = self._io.read_s4le()

        @property
        def vert_frame_name(self):
            if hasattr(self, '_m_vert_frame_name'):
                return self._m_vert_frame_name

            if self.offset_vert_frame_name != -1:
                _pos = self._io.pos()
                self._io.seek(self.offset_vert_frame_name)
                self._m_vert_frame_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
                self._io.seek(_pos)

            return getattr(self, '_m_vert_frame_name', None)


    class CpjChunkHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x53\x45\x51\x42":
                raise kaitaistruct.ValidationNotEqualError(b"\x53\x45\x51\x42", self.magic, self._io, u"/types/cpj_chunk_header/seq/0")
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
        def frames(self):
            if hasattr(self, '_m_frames'):
                return self._m_frames

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_frames)
            self._m_frames = []
            for i in range(self._root.num_frames):
                self._m_frames.append(Seq.Frame(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_frames', None)

        @property
        def bone_rotate(self):
            if hasattr(self, '_m_bone_rotate'):
                return self._m_bone_rotate

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_bone_rotate)
            self._m_bone_rotate = []
            for i in range(self._root.num_bone_rotate):
                self._m_bone_rotate.append(Seq.BoneRotate(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_bone_rotate', None)

        @property
        def bone_info(self):
            if hasattr(self, '_m_bone_info'):
                return self._m_bone_info

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_bone_info)
            self._m_bone_info = []
            for i in range(self._root.num_bone_info):
                self._m_bone_info.append(Seq.BoneInfo(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_bone_info', None)

        @property
        def bone_scale(self):
            if hasattr(self, '_m_bone_scale'):
                return self._m_bone_scale

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_bone_scale)
            self._m_bone_scale = []
            for i in range(self._root.num_bone_scale):
                self._m_bone_scale.append(Seq.BoneScale(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_bone_scale', None)

        @property
        def bone_translate(self):
            if hasattr(self, '_m_bone_translate'):
                return self._m_bone_translate

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_bone_translate)
            self._m_bone_translate = []
            for i in range(self._root.num_bone_translate):
                self._m_bone_translate.append(Seq.BoneTranslate(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_bone_translate', None)

        @property
        def events(self):
            if hasattr(self, '_m_events'):
                return self._m_events

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_events)
            self._m_events = []
            for i in range(self._root.num_events):
                self._m_events.append(Seq.Event(self._io, self, self._root))

            self._io.seek(_pos)
            return getattr(self, '_m_events', None)


    class BoneTranslate(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.bone_index = self._io.read_u2le()
            self.reserved = self._io.read_u2le()
            self.translate = Seq.Vec3f(self._io, self, self._root)


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


    class BoneScale(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.bone_index = self._io.read_u2le()
            self.reserved = self._io.read_u2le()
            self.scale = Seq.Vec3f(self._io, self, self._root)


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


