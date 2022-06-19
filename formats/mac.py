# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

from pkg_resources import parse_version
import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if parse_version(kaitaistruct.__version__) < parse_version('0.9'):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Mac(KaitaiStruct):
    """A model actor represents a combination of various resources and represents
    the model as a whole.  The initial configuration of a model actor is done
    with model actor configuration chunks.  These chunks contain a series of
    text commands which are executed to change the properties of the actor.
    The commands are used to set up a model's active resource chunks as well as
    any other miscellaneous properties desired.
    
    The chunk is broken up into "sections", each of which contains a simple
    set of text commands that are executed in order.  The separation into sections
    allows user extension information to be stored with the actor, within a
    different section.  Any sections not explicitly requested by an editing
    program should be preserved intact without alteration.
    
    Model actor chunks can be stored in files independent of a full model project
    (using the .MAC extension; see the Overview section above), for the purposes
    of import and export convenience.  Although they can be stored outside a
    full project, they are often meaningless in such a state.  Actor chunks are
    most useful within the context of the full project with which they are
    associated.
    
    .. seealso::
       Cannibal/CpjFmt.h
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.cpj_chunk_header = Mac.CpjChunkHeader(self._io, self, self._root)
        self.num_sections = self._io.read_u4le()
        self.data_offset_sections = self._io.read_u4le()
        self.num_commands = self._io.read_u4le()
        self.data_offset_commands = self._io.read_u4le()
        self._raw_data_block = self._io.read_bytes_full()
        _io__raw_data_block = KaitaiStream(BytesIO(self._raw_data_block))
        self.data_block = Mac.DataBlock(_io__raw_data_block, self, self._root)

    class CpjChunkHeader(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x4D\x41\x43\x42":
                raise kaitaistruct.ValidationNotEqualError(b"\x4D\x41\x43\x42", self.magic, self._io, u"/types/cpj_chunk_header/seq/0")
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
        def sections(self):
            if hasattr(self, '_m_sections'):
                return self._m_sections if hasattr(self, '_m_sections') else None

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_sections)
            self._m_sections = [None] * (self._root.num_sections)
            for i in range(self._root.num_sections):
                self._m_sections[i] = Mac.Section(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_sections if hasattr(self, '_m_sections') else None

        @property
        def commands(self):
            if hasattr(self, '_m_commands'):
                return self._m_commands if hasattr(self, '_m_commands') else None

            _pos = self._io.pos()
            self._io.seek(self._root.data_offset_commands)
            self._m_commands = [None] * (self._root.num_commands)
            for i in range(self._root.num_commands):
                self._m_commands[i] = Mac.Command(self._io, self, self._root)

            self._io.seek(_pos)
            return self._m_commands if hasattr(self, '_m_commands') else None


    class Section(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_name = self._io.read_u4le()
            self.num_commands = self._io.read_u4le()
            self.first_command = self._io.read_u4le()

        @property
        def name(self):
            if hasattr(self, '_m_name'):
                return self._m_name if hasattr(self, '_m_name') else None

            _pos = self._io.pos()
            self._io.seek(self.offset_name)
            self._m_name = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)
            return self._m_name if hasattr(self, '_m_name') else None


    class Command(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.offset_command_str = self._io.read_u4le()

        @property
        def command_str(self):
            if hasattr(self, '_m_command_str'):
                return self._m_command_str if hasattr(self, '_m_command_str') else None

            _pos = self._io.pos()
            self._io.seek(self.offset_command_str)
            self._m_command_str = (self._io.read_bytes_term(0, False, True, True)).decode(u"ASCII")
            self._io.seek(_pos)
            return self._m_command_str if hasattr(self, '_m_command_str') else None


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


