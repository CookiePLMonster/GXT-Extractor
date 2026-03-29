import argparse
import sys
import os
import gta.gxt

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

parser = argparse.ArgumentParser(
    description="A tool for extracting the GXT files from the GTA games.")

parser.add_argument('gxt', help='path to the GXT file to extract')
parser.add_argument('-c', '--charmap', default='charmap.txt', help='path to the character map file (default: %(default)s)')

args = parser.parse_args()

outDirName = os.path.splitext(args.gxt)[0]
def readOutTable(gxt, charmap, reader, name):
    with open(os.path.join(outDirName, name + '.txt'), 'w', encoding='utf-8') as f:
        for text in reader.parseTKeyTDat(gxt, charmap):
            f.write( text[0] + '\t' + text[1] + '\n' )

with open(args.gxt, 'rb') as gxt:
    gxtversion = gta.gxt.getVersion(gxt)

    if not gxtversion:
        eprint('Unknown GXT version!')
        exit(1)

    print(f"Detected GXT version: {gxtversion}")

    charmap = gta.gxt.readCharmap(args.charmap)
    if not charmap:
        eprint('Invalid character map! It must be a file with 256 tab-delimited entries')
        exit(1)

    gxtReader = gta.gxt.getReader(gxtversion)

    Tables = []
    if gxtReader.hasTables():
        Tables = gxtReader.parseTables(gxt)

    os.makedirs(outDirName, exist_ok=True)
    readOutTable(gxt, charmap, gxtReader, 'MAIN')

    if Tables:
        for t in Tables[1:]:
            gxt.seek(t[1])
            readOutTable(gxt, charmap, gxtReader, t[0])