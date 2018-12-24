import sys
import os
import errno
import gta.gxt

args = sys.argv[1:]
outDirName = os.path.splitext(args[0])[0]

def createOutputDir(path):
    try:
        os.makedirs( path )
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def readOutTable(gxt, reader, name):
    createOutputDir(os.path.join(outDirName, name))

    with open(os.path.join(outDirName, name, name + '.txt'), 'w', encoding='utf-8') as f:
        for text in reader.parseTKeyTDat(gxt):
            f.write( text[0] + '\t' + text[1] + '\n' )


# TODO: Parse arguments
with open(args[0], 'rb') as gxt:
    gxtversion = gta.gxt.getVersion(gxt)

    if not gxtversion:
        print('Unknown GXT version!', file=sys.stderr)
        exit(1)

    print("Detected GXT version: {}".format(gxtversion))

    gxtReader = gta.gxt.getReader(gxtversion)
    
    Tables = []
    if gxtReader.hasTables():
        Tables = gxtReader.parseTables(gxt)

    readOutTable(gxt, gxtReader, 'MAIN')

    if Tables:
        for t in Tables[1:]:
            gxt.seek(t[1])
            readOutTable(gxt, gxtReader, t[0])