import struct
from collections import OrderedDict

class VC:
    def readData(self, file, charmap):
        data = OrderedDict()
        tables = _parseTables(file)
        for table in tables:
            file.seek(table[1])
            size = _findBlock(file, b'TKEY')

            TKey = []
            for i in range(int(size / 12)): # TKEY entry size - 12
                TKey.append( struct.unpack('<I8s', file.read(12)) )

            datSize = _findBlock(file, b'TDAT')
            TDat = file.read(datSize)

            tabl_entries = OrderedDict()

            for entry in TKey:
                key = entry[1]
                value_data = TDat[entry[0]:].split(b'\x00\x00', 1)[0]
                value = ''.join(charmap[value_data[i]] for i in range(0, len(value_data), 2))
                tabl_entries[key.split(b'\x00', 1)[0].decode()] = value

            data[table[0]] = tabl_entries

        return data

class SA:
    def __init__(self, char_size):
        self.char_size = char_size
        self.term_char = b'\x00' * char_size

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
                value_data = TDat[entry[0]:].split(self.term_char, 1)[0]
                value = ''.join(charmap[value_data[i]] for i in range(0, len(value_data), self.char_size))
                tabl_entries[key] = value

            data[table[0]] = tabl_entries

        return data

def readGxtFile(gxt_path, charmap_path):
    charmap = ['\x00'] * 32
    with open(charmap_path, 'r', encoding='utf-8') as f:
        for line in f:
            charmap.extend(line.rstrip('\r\n').split('\t'))

    with open(gxt_path, 'rb') as gxt:
        gxt_version, reader = _getReader(gxt)
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

def _getReader(file):
    bytes = file.peek(8) [:8]

    # SA
    word1, word2 = struct.unpack('<HH', bytes[:4])
    if word1 == 4 and bytes[4:] == b'TABL':
        if word2 == 8:
            return 'gtasa', SA(1)
        if word2 == 16:
            return 'gtasa-mobile', SA(2)

    if bytes[:4] == b'TABL':
        return 'gtavc', VC()

    return 'unknown', None
