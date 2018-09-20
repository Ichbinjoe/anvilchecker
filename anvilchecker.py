#!/usr/bin/python3

import mmap
import os
import re
import struct
import sys
import zlib

def check_file(file_name):
    print("Checking file {}".format(file_name))
    with open(file_name, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        m = re.search('r\.(-?[0-9]+)\.(-?[0-9]+)\.mca', file_name)
        if m is None:
            check_memory_map(mm)
        else:
            check_memory_map(mm, int(m.group(1)), int(m.group(2)))

def section_of_mm(mm, snum, scnt):
    return mm[(snum * 4096):((snum + scnt) * 4096)]

def display_sector_use(ownership, sectors):
    s = ""
    for i in range(sectors):
        if i in ownership:
            s += "+"
        else:
            s += "."
        if (i + 1) % 50 == 0:
            s += '\n'
    print(s)

def check_memory_map(mm, rx=0, rz=0):
    # so the plan is to basically to go through and validate that the offsets
    # are correct

    section_ownerships = {
            0: "Offsets",
            1: "Timestamps",
    }

    if len(mm) % 4096 != 0:
        print("!!INVALID LENGTH!! File is of invalid length {}!".format(len(mm)))

    sectors = len(mm) // 4096
    print("File has {} bytes for {} sectors.".format(len(mm), sectors))

    offsets = section_of_mm(mm, 0, 1)

    # we are reversing this so that the offset_number increases nicely
    for z in range(32):
        for x in range(32):
            identifier = "{}, {}".format(x, z)
            if rx != 0 or rz != 0:
                identifier += " ({}, {})".format(x + (rx * 32), z + (rz * 32))

            offset_number = x + (z * 32)

            offset_value = struct.unpack_from(">I", offsets, offset_number * 4)[0]
            section_offset = offset_value >> 8
            sector_count = offset_value & 0xff

            had_diagnostic = False
            def print_diagnostic():
                nonlocal had_diagnostic
                if not had_diagnostic:
                    had_diagnostic = True
                    print("{} Offset: {} ({}) Count: {} ({}) (to {})"
                            .format(identifier, 
                                section_offset, 
                                section_offset * 4096, 
                                sector_count, 
                                sector_count * 4096, 
                                (section_offset + sector_count) * 4096))

            if section_offset == 0 and sector_count == 0:
                continue

            # Make sure the chunks _actually exist_
            last_sector_p1 = section_offset + sector_count
            if last_sector_p1 > sectors:
                print_diagnostic()
                print("!!OUT OF FILE!! Chunk sectors were found to overrun the file length. (Needed {}, has {})".format(last_sector_p1, sectors))

            # Check for collisions
            has_collision = False
            for i in range(section_offset, section_offset + sector_count):
                if i in section_ownerships:
                    print_diagnostic()
                    print("!!COLLISION!! Collision found! At sector {}, ({}) and ({}) collided.".format(identifier, section_ownerships[i]))
                    has_collision = True
                else:
                    section_ownerships[i] = identifier

            # Next, check to ensure that the chunk looks formatted correctly
            cdata = section_of_mm(mm, section_offset, sector_count)
            
            len_of_sections = struct.unpack_from(">I", cdata, 0)[0] + 4 # why plus four? must account for length field
            if len_of_sections > sector_count * 4096:
                print_diagnostic()
                print("!!OVERRUN!! Length reported longer than sectors allocated for it. (Length: {}, Sectors: {}, Sectors Bytes: {})"
                        .format(len_of_sections, sector_count, sector_count * 4096))
            elif len_of_sections < (sector_count - 1) * 4096:
                print_diagnostic()
                print("!!UNDERRUN!! Length reported shorter than the sectors allocated for it. (Length: {}, Sectors: {}, Sectors Bytes: {})"
                        .format(len_of_sections, sector_count, sector_count * 4096))

            compression = struct.unpack_from(">B", cdata, 4)[0]
           
            if compression == 1:
                print_diagnostic()
                print("!!UNUSED COMPRESSION!! While this is a valid compression type, this is typically an error since no one uses it (GZip, 1)!")
            elif compression == 2:
                data = cdata[5:len_of_sections]
                try:
                    zlib.decompress(data)
                except zlib.error:
                    print_diagnostic()
                    print("!!ZLIB ERROR!! ZLib wasn't able to properly decompress the data stream - may be indicative of a corrupted chunk.")
            else:
                print_diagnostic()
                print("!!UNKNOWN COMPRESSION!! We couldn't figure out how this chunk was compressed! It had this ID: {}".format(compression))
    
    for i in range(sectors):
        if i not in section_ownerships:
            cdata = section_of_mm(mm, i, 1)
            compression = struct.unpack_from(">B", cdata, 4)[0]
            if compression == 1:
                print("--Unused sector {} had 1 as compression... mislabeled section?".format(i))


    display_sector_use(section_ownerships, sectors)
           
def check_file_or_dir(file_name):
    if os.path.isdir(file_name):
        for c_name in os.listdir(file_name):
            c_name = os.path.join(file_name, c_name)
            if os.path.isfile(c_name):
                check_file(c_name)
    else:
        check_file(file_name)

def main():
    if len(sys.argv) > 1:
        check_file_or_dir(sys.argv[1])
    else:
        check_file_or_dir(os.getcwd())

if __name__ == "__main__":
    main()

