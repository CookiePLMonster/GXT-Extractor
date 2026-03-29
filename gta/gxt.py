import struct
from abc import ABC, abstractmethod
from collections import OrderedDict

class DecoderBase(ABC):
    @abstractmethod
    def readData(self, file, charmap):
        pass

    def extendCharmap(self, charmap):
        return charmap

class III(DecoderBase):
    def readData(self, file, charmap):
        data = OrderedDict()
        data['MAIN'] = self._readOneTable(file, charmap)

        return data

    def _readOneTable(self, file, charmap):
        size = _findBlock(file, b'TKEY')

        TKey = []
        for _ in range(int(size / 12)): # TKEY entry size - 12
            TKey.append( struct.unpack('<I8s', file.read(12)) )

        datSize = _findBlock(file, b'TDAT')
        TDat = file.read(datSize)

        tabl_entries = OrderedDict()

        for entry in TKey:
            key = entry[1]
            value_data = _trimString(TDat[entry[0]:], 2)
            value = ''.join(charmap[int.from_bytes(value_data[i:i+2], byteorder='little')] for i in range(0, len(value_data), 2))
            tabl_entries[key.split(b'\x00', 1)[0].decode()] = value

        return tabl_entries

class VC(III):
    def readData(self, file, charmap):
        data = OrderedDict()
        tables = _parseTables(file)
        for table in tables:
            file.seek(table[1])
            data[table[0]] = self._readOneTable(file, charmap)

        return data

class GTA2(III):
    def extendCharmap(self, charmap):
        charmap[0x216B] = '{Krishna} '
        charmap[0x216C] = '{Loony} '
        charmap[0x216D] = '{Russian} '
        charmap[0x216E] = '{Neutral} '
        charmap[0x2170] = '{Police} '
        charmap[0x2172] = '{Redneck} '
        charmap[0x2173] = '{Scientist} '
        charmap[0x2179] = '{Yakuza} '
        charmap[0x217A] = '{Zaibatsu} '

        # This is broken, but was intended to be Scientist
        charmap[0x2153] = '{???} '
        return charmap

class SA(DecoderBase):
    def __init__(self, char_size):
        self.char_size = char_size

    def readData(self, file, charmap):
        data = OrderedDict()
        tables = _parseTables(file)
        for table in tables:
            file.seek(table[1])
            size = _findBlock(file, b'TKEY')

            TKey = []
            for _ in range(int(size / 8)): # TKEY entry size - 8
                TKey.append( struct.unpack('<II', file.read(8)) )

            datSize = _findBlock(file, b'TDAT')
            TDat = file.read(datSize)

            tabl_entries = OrderedDict()

            for entry in TKey:
                key = f'0x{entry[1]:08X}'
                value_data = _trimString(TDat[entry[0]:], self.char_size)
                value = ''.join(charmap[int.from_bytes(value_data[i:i+self.char_size], byteorder='little')] for i in range(0, len(value_data), self.char_size))
                tabl_entries[key] = value

            data[table[0]] = tabl_entries

        return data

def readGxtFile(gxt_path, charmap_path):
    charmap_list = []
    with open(charmap_path, 'r', encoding='utf-8') as f:
        for line in f:
            charmap_list.extend(line.rstrip('\r\n').split('\t'))
    charmap = {index + 32: value for index, value in enumerate(charmap_list)}

    with open(gxt_path, 'rb') as gxt:
        gxt_version, reader = _getReader(gxt)
        charmap = reader.extendCharmap(charmap)
        return gxt_version, reader.readData(gxt, charmap)

# Internal functions
def _findBlock(stream, block):
    while stream.peek(4) [:4] != block:
        stream.read(1)

    _, size = struct.unpack('<4sI', stream.read(8))

    return size

def _parseTables(stream):
    size = _findBlock(stream, b'TABL')
    Tables = []

    for i in range(int(size / 12)): # TABL entry size - 12
        rawName, offset = struct.unpack('<8sI', stream.read(12))
        Tables.append( (rawName.split(b'\x00', 1)[0].decode(), offset) )

    return Tables

def _trimString(string, char_size):
    term = b'\x00' * char_size
    for i in range(0, len(string) + 1 - char_size, char_size):
        if string[i:i+char_size] == term:
            string = string[:i]
            break

    return string

def _getReader(file):
    bytes = file.peek(8) [:8]

    # SA
    word1, word2 = struct.unpack('<HH', bytes[:4])
    if word1 == 4 and bytes[4:] == b'TABL':
        if word2 == 8:
            return 'gtasa', SA(1)
        if word2 == 16:
            return 'gtasa-mobile', SA(2)

    # III/VC
    if bytes[:4] == b'TABL':
        return 'gtavc', VC()
    elif bytes[:4] == b'TKEY':
        return 'gtaiii', III()

    # GTA2
    magic, language, version = struct.unpack('<3scH', bytes[:6])
    if magic == b'GBL' and version == 100:
        return f'gta2 ({language.decode('ascii')})', GTA2()

    return 'unknown', None
