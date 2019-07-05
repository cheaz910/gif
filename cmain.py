#!/usr/bin/python3
import argparse
import GifInfo
import textwrap
import os
import sys
from PIL import Image

DESCRIPTION_TYPES = ['raw_data', 'deciphered_data', 'rgb_data']


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument('filename', type=str, help='Name of gif file')
    group.add_argument('-b', '--bmp', type=str, dest='bmp_arg',
                       help='Create bmp frames in [filename] directory')
    group.add_argument('description', type=str, nargs='?',
                       help='Print gif description.\n'
                            'Types:\n\t%s' % '\n\t'.join(DESCRIPTION_TYPES))
    args = parser.parse_args()
    try:
        if args.description:
            print_gif_objects(args.filename, args.description)
        if args.bmp_arg:
            create_bmp_frames(args.filename, args.bmp_arg)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(int(str(e)))
    except KeyError:
        print('Error: decode LZW', file=sys.stderr)
        sys.exit(17)
    except IndexError as e:
        print(e, file=sys.stderr)
        sys.exit(18)


def print_raw_data(gif):
    print('Logical Screen Descriptor:\n    {}\n'.format(gif.lsd.raw_data))
    for i in gif.program_extensions:
        print('Program Extension {}:'.format(i.app_id), end='\n    ')
        if i.app_id == 'XMP Data':
            print('{}[xmp packet]00'.format(i.raw_data[:28]))
        else:
            print(i.raw_data)
        print()
    for counter, descr in enumerate(gif.image_descriptors):
        print("Image Descriptor {}:\n    {}".format(counter, descr.raw_data))
        if descr.graphic_extension:
            raw_data = descr.graphic_extension.raw_data
            print("Graphic Extension {}:\n    {}".format(counter, raw_data))
        raw_data = descr.graphic_block.raw_data
        print("Graphic Block {}:\n    {}\n".format(counter, raw_data))


def print_deciphered_data(gif):
    print('Logical Screen Descriptor:\n{}\n'.format(gif.lsd))
    for i in gif.program_extensions:
        print('Program Extension {}:'.format(i.app_id), end='\n    ')
        print('%s\n' % i)
    for counter, descr in enumerate(gif.image_descriptors):
        print('Frame {}:\n{}'.format(counter, descr))
        if descr.graphic_extension:
            print('Graphic Extension of Frame {}:\n'
                  '{}'.format(counter, descr.graphic_extension))
        print()


def print_rgb_data(gif):
    print(' Global Color Table:', end='\n    ')
    rgb = gif.gct.raw_data
    if rgb:
        print(' '.join([rgb[i:i + 6] for i in range(0, len(rgb), 6)]))
        print()
    else:
        print('    empty\n')
    for counter, descr in enumerate(gif.image_descriptors):
        if descr.lct:
            print(' Local Color Table of Frame {}:'.format(counter), end='\n')
            rgb = descr.lct.raw_data
            print(' '.join([rgb[i:i + 6] for i in range(0, len(rgb), 6)]))
        print()


def print_gif_objects(filename, descr_type):
    if descr_type not in DESCRIPTION_TYPES:
        print('Error: undefined type of description', file=sys.stderr)
        return
    gif = GifInfo.GifInfo(filename)
    if descr_type == 'raw_data':
        print_raw_data(gif)
    elif descr_type == 'deciphered_data':
        print_deciphered_data(gif)
    elif descr_type == 'rgb_data':
        print_rgb_data(gif)


def create_bmp_frames(filename, arg):
    gif = GifInfo.GifInfo(filename)
    directory = get_not_existed_dir(filename)
    start, end = get_segment_of_frames(arg, len(gif.frames))
    os.mkdir(directory)  # get_not_existed_dir выбирает имя директории
    for x in range(start, end):
        size = (int(gif.width, 16), int(gif.height, 16))
        img = Image.new('RGB', size, "white")
        pixels = img.load()
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                rgb = textwrap.wrap(gif.frames[x][j][i], 2)
                pixels[i, j] = tuple(map(lambda z: int(z, 16), rgb))
        img.save('{}/{}.bmp'.format(directory, x + 1))
    print('Directory: {}'.format(directory))


def get_segment_of_frames(arg, count):
    segment = arg.split(':')
    if len(segment) == 1:
        frame_number = int(segment[0])
        if not 0 < frame_number <= count:
            print("Error: this frame doesn't exist", file=sys.stderr)
            sys.exit(2)
        return int(segment[0]) - 1, int(segment[0])
    elif len(segment) == 2:
        start = int(segment[0] or '1')
        if segment[1] == '':
            end = count
        else:
            end = int(segment[1])
        if not 0 < start <= count or not 0 < end <= count:
            print("Error: this frames don't exist", file=sys.stderr)
            sys.exit(2)
        if start > end:
            print("Error: start > end", file=sys.stderr)
            sys.exit(2)
        return start - 1, end
    print("Error: bad format of --bmp argument", file=sys.stderr)
    sys.exit(2)


def get_not_existed_dir(filename):
    directory = os.path.splitext(filename)[0]
    i = 0
    original_directory = directory
    while os.path.exists(directory):
        directory = original_directory + '({})'.format(i)
        i += 1
    return directory


if __name__ == '__main__':
    main()
