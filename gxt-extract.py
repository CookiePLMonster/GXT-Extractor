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

gxt_version, gxt_data = gta.gxt.readGxtFile(args.gxt, args.charmap)
if not gxt_data:
    eprint('Unknown GXT version!')
    exit(1)

print(f"Detected GXT version: {gxt_version}")

output_dir = os.path.splitext(args.gxt)[0]
os.makedirs(output_dir, exist_ok=True)

for table_name, table_data in gxt_data.items():
    with open(os.path.join(output_dir, table_name + '.txt'), 'w', encoding='utf-8') as f:
        for key, value in table_data.items():
            f.write(f'{key}\t{value}\n')
