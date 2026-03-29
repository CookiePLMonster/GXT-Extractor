import struct
import os

class VC:
    def hasTables(self):
        return True

    def parseTables(self, stream):
        return _parseTables(stream)

    def parseTKeyTDat(self, stream, charmap):
        size = findBlock(stream, b'TKEY')

        TKey = []
        for i in range(int(size / 12)): # TKEY entry size - 12
            TKey.append( struct.unpack('<I8s', stream.read(12)) )

        datSize = findBlock(stream, b'TDAT')
        TDat = stream.read(datSize)

        Entries = []

        for entry in TKey:
            key = entry[1]
            value_data = TDat[entry[0]:].split(b'\x00\x00', 1)[0]
            value = ''.join(charmap[value_data[i]] for i in range(0, len(value_data), 2))
            Entries.append( (key.split(b'\x00', 1)[0].decode(), value) )

        return Entries

class SA:
    def __init__(self, char_size):
        self.char_size = char_size
        self.term_char = b'\x00' * char_size

    def hasTables(self):
        return True

    def parseTables(self, stream):
        return _parseTables(stream)

    def parseTKeyTDat(self, stream, charmap):
        size = findBlock(stream, b'TKEY')

        TKey = []
        for i in range(int(size / 8)): # TKEY entry size - 8
            TKey.append( struct.unpack('<II', stream.read(8)) )

        datSize = findBlock(stream, b'TDAT')
        TDat = stream.read(datSize)

        Entries = []

        for entry in TKey:
            key = f'0x{entry[1]:08X}'
            value_data = TDat[entry[0]:].split(self.term_char, 1)[0]
            value = ''.join(charmap[value_data[i]] for i in range(0, len(value_data), self.char_size))

            Entries.append( (key, value) )

        return Entries


def findBlock(stream, block):
    while stream.peek(4) [:4] != block:
        stream.seek(1, os.SEEK_CUR)

    _, size = struct.unpack('<4sI', stream.read(8))

    return size

def getVersion(stream):
    bytes = stream.peek(8) [:8]

    # SA
    word1, word2 = struct.unpack('<HH', bytes[:4])
    if word1 == 4 and bytes[4:] == b'TABL':
        if word2 == 8:
            return 'sa'
        if word2 == 16:
            return 'sa-mobile'

    if bytes[:4] == b'TABL':
        return 'vc'

    return None

def getReader(version):
    if version == 'vc':
        return VC()
    if version == 'sa':
        return SA(1)
    if version == 'sa-mobile':
        return SA(2)
    return None

def readCharmap(path):
    entries = ['\x00'] * 32
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            entries.extend(line.rstrip('\r\n').split('\t'))

    return entries

# Internal functions
def _parseTables(stream):
    size = findBlock(stream, b'TABL')
    Tables = []

    for i in range(int(size / 12)): # TABL entry size - 12
        rawName, offset = struct.unpack('<8sI', stream.read(12))
        Tables.append( (rawName.split(b'\x00', 1)[0].decode(), offset) )

    return Tables