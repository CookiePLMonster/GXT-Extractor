import struct
import os

class VC:    
    def hasTables(self):
        return True

    def parseTables(self, stream):
        return _parseTables(stream)

    def parseTKeyTDat(self, stream):
        size = findBlock(stream, 'TKEY')
        
        TKey = []
        for i in range(int(size / 12)): # TKEY entry size - 12
            TKey.append( struct.unpack('I8s', stream.read(12)) )
        
        datSize = findBlock(stream, 'TDAT')
        TDat = stream.read(datSize)

        Entries = []

        for entry in TKey:
            key = entry[1]
            value = TDat[entry[0]:].decode('utf-16').split('\x00', 1) [0]
            Entries.append( (key.rstrip(b'\x00').decode(), value) ) # TODO: charmap
        
        return Entries

class SA:    
    def hasTables(self):
        return True

    def parseTables(self, stream):
        return _parseTables(stream)

    def parseTKeyTDat(self, stream):
        size = findBlock(stream, 'TKEY')
        
        TKey = []
        for i in range(int(size / 8)): # TKEY entry size - 8
            TKey.append( struct.unpack('II', stream.read(8)) )
        
        datSize = findBlock(stream, 'TDAT')
        TDat = stream.read(datSize)

        Entries = []

        for entry in TKey:
            key = f'0x{entry[1]:08X}'
            value = TDat[entry[0]:].decode('cp1252').split('\x00', 1) [0]

            Entries.append( (key, value) ) # TODO: charmap
        
        return Entries


def findBlock(stream, block):
    while stream.peek(4) [:4] != block.encode():
        stream.seek(1, os.SEEK_CUR)

    _, size = struct.unpack('4sI', stream.read(8))

    return size

def getVersion(stream):
    bytes = stream.peek(8) [:8]

    # SA
    word1, word2 = struct.unpack('HH', bytes[:4])
    if word1 == 4 and bytes[4:] == 'TABL'.encode():
        if word2 == 8:
            return 'sa'
        if word2 == 16:
            return 'sa-mobile'
    
    if bytes[:4] == 'TABL'.encode():
        return 'vc'
    
    return None

def getReader(version):
    if version == 'vc':
        return VC()
    if version == 'sa':
        return SA()
    return None

# Internal functions
def _parseTables(stream):
    size = findBlock(stream, 'TABL')
    Tables = []
        
    for i in range(int(size / 12)): # TABL entry size - 12
        rawName, offset = struct.unpack('8sI', stream.read(12))
        Tables.append( (rawName.rstrip(b'\0').decode(), offset) )
    
    return Tables