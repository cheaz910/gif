import copy
import codecs
import math
import sys


EXCEPTION_MESSAGES = {3: 'Error: logical screen descriptor is wrong, len < 26',
                      4: 'Error: wrong header',
                      5: 'Error: wrong field(MC)',
                      6: 'Error: wrong field(size of graphic extension)',
                      8: 'Error: file ends prematurely',
                      9: 'Error: undefined byte',
                      10: 'Error: wrong name of program extension',
                      11: 'Error: undefined program id',
                      12: 'Error: bad format of program extension',
                      13: 'Error: wrong field of size block in netscape '
                          'extension',
                      14: 'Error: undefined byte',
                      15: 'Error: undefined extension',
                      16: 'Error: undefined bytes in decode LZW'}


class LogicalScreenDescriptor:
    def __init__(self, hex_bytes):
        if len(hex_bytes) < 26:
            raise ValueError(EXCEPTION_MESSAGES[3])
        self.header = codecs.decode(hex_bytes[:12], 'hex').decode('utf8')
        if self.header != "GIF89a" and self.header != "GIF87a":
            raise ValueError(EXCEPTION_MESSAGES[4])
        self.width = GifInfo.swap_pixels(hex_bytes[12:16])
        self.height = GifInfo.swap_pixels(hex_bytes[16:20])
        self.packed_fields = bin(int(hex_bytes[20:22], 16))[2:].rjust(8, '0')
        self.is_global_table = int(self.packed_fields[0])
        self.color_resolution = self.packed_fields[1:4]
        self.is_sorted_pal = int(self.packed_fields[4], 2)
        self.size_table = int(math.pow(2, int(self.packed_fields[5:8], 2) + 1))
        self.index_bg_color = hex_bytes[22:24]
        self.ratio = hex_bytes[24:26]
        self.size_block = 26
        self.raw_data = hex_bytes[:26]

    def __str__(self):
        return ("\tHeader:{}\n"
                "\tWidth={}; Height={}\n"
                "\tGlobal Table:{}\n"
                "\tColor Resolution:{}\n"
                "\tIs global table sorted:{}\n"
                "\tGlobal table size:{}\n"
                "\tIndex of background color:{}\n"
                "\tRatio:{}".format(self.header,
                                    int(self.width, 16),
                                    int(self.height, 16),
                                    bool(self.is_global_table),
                                    self.color_resolution,
                                    bool(self.is_sorted_pal),
                                    self.size_table,
                                    self.index_bg_color,
                                    self.ratio))


class ColorTable:
    def __init__(self, hex_bytes, is_table, size_table):
        self.color_table = []
        self.size_block = 0
        if is_table:
            size_global_table = size_table
            self.color_table = ColorTable._get_colors(hex_bytes,
                                                      size_global_table)
            self.size_block += size_global_table * 6
        self.raw_data = hex_bytes[:self.size_block]

    def __str__(self):
        return "Size of color table:{}".format(self.size_block)

    @staticmethod
    def _get_colors(hex_bytes, size):
        start = 0
        triad_size = 6
        triads = []
        for i in range(1, size + 1):
            triads.append(hex_bytes[start:start + triad_size])
            start += triad_size
        return triads


class ImageDescriptor:
    def __init__(self, hex_bytes):
        self.raw_data = hex_bytes[:20]
        hex_bytes = hex_bytes[2:]
        self.left = GifInfo.swap_pixels(hex_bytes[:4])
        self.top = GifInfo.swap_pixels(hex_bytes[4:8])
        self.width = GifInfo.swap_pixels(hex_bytes[8:12])
        self.height = GifInfo.swap_pixels(hex_bytes[12:16])
        packed_fields = bin(int(hex_bytes[16:18], 16))[2:].rjust(8, '0')
        self.is_local_table = int(packed_fields[0], 2)
        self.is_interplace = packed_fields[1]
        self.is_sorted_pal = packed_fields[2]
        self.size_local_table = int(math.pow(2, int(packed_fields[5:], 2) + 1))
        self.size_block = 18
        self.graphic_block = None
        self.graphic_extension = None

    def __str__(self):
        return ("\tCoordinates of the left top corner:({},{})\n"
                "\tWidth={}; Height={}\n"
                "\tIs local table:{}\n"
                "\tIs interplace:{}\n"
                "\tIs sorted color table:{}\n"
                "\tSize of local color table:{}\n"
                "\tIs graphic extension:{}".format(
                    int(self.left, 16),
                    int(self.top, 16),
                    int(self.width, 16),
                    int(self.height, 16),
                    bool(self.is_local_table),
                    bool(self.is_interplace),
                    bool(self.is_sorted_pal),
                    self.size_local_table,
                    bool(self.graphic_extension)))


class GraphicBlock:
    def __init__(self, hex_bytes):
        self.mc = int(hex_bytes[:2], 16)
        if self.mc < 2 or self.mc > 8:
            raise ValueError(EXCEPTION_MESSAGES[5])
        subblocks_info = GifInfo.get_N_subblocks(hex_bytes)
        self.subblocks = subblocks_info[0]
        self.size_block = subblocks_info[1]
        self.raw_data = hex_bytes[:self.size_block]


class GraphicExtension:
    def __init__(self, hex_bytes):
        self.raw_data = hex_bytes[:16]
        hex_bytes = hex_bytes[2:]
        fixed_size_block = hex_bytes[2:4]
        if fixed_size_block != '04':
            raise ValueError(EXCEPTION_MESSAGES[6])
        hex_bytes = hex_bytes[4:]
        packed_fields = bin(int(hex_bytes[:2], 16))[2:].rjust(8, '0')
        self.disposal_method = packed_fields[3:6]
        self.user_input = packed_fields[6]
        self.transparency_flag = packed_fields[7]
        self.delay = int(GifInfo.swap_pixels(hex_bytes[2:6]), 16)
        self.number_transparency_color = int(hex_bytes[6:8], 16)
        self.size_block = 14

    def __str__(self):
        return ("\tDisposal method:{}\n"
                "\tUser input flag:{}\n"
                "\tTransparency flag:{}\n"
                "\tNumber of transparency color:{}"
                "\tDelay:{}\n".format(self.disposal_method,
                                      self.user_input,
                                      self.transparency_flag,
                                      self.delay,
                                      self.number_transparency_color))


class CommentExtension:
    def __init__(self, hex_bytes):
        self.subblock, self.size_block = GifInfo.get_N_subblocks(hex_bytes)
        self.raw_data = hex_bytes[:self.size_block]


class ProgramExtension:
    def __init__(self, hex_bytes):
        self.raw_data = hex_bytes[:2]
        hex_bytes = hex_bytes[2:]
        subblock_size = hex_bytes[2:4]
        if subblock_size != '0b':
            raise ValueError(EXCEPTION_MESSAGES[10])
        self.app_id = codecs.decode(hex_bytes[4:20], 'hex').decode('utf8')
        self.code_id = codecs.decode(hex_bytes[20:26], 'hex').decode('utf8')
        if self.app_id == 'XMP Data':
            app_info = self.read_xmp_packet(hex_bytes[26:])
        elif self.app_id == 'NETSCAPE':
            app_info = self.process_ext_program_netscape(hex_bytes)
        else:
            raise ValueError(EXCEPTION_MESSAGES[11])
        self.subblock, self.size_block = app_info
        if hex_bytes[self.size_block - 2:self.size_block] != '00':
            raise ValueError(EXCEPTION_MESSAGES[12])
        self.raw_data += hex_bytes[:self.size_block]

    def __str__(self):
        return ("\tApplication id:{}\n"
                "\tApplication code:{}".format(self.app_id, self.code_id))

    @staticmethod
    def process_ext_program_netscape(hex_bytes):
        subblock_size = hex_bytes[26:28]
        if subblock_size != '03':
            raise ValueError(EXCEPTION_MESSAGES[13])
        subblock_end = 28 + int(subblock_size, 16) * 2
        subblock = hex_bytes[28:subblock_end]
        size_block = subblock_end + 2
        return subblock, size_block

    @staticmethod
    def read_xmp_packet(hex_bytes):
        byte = hex_bytes[:2]
        start = 2
        need_byte = 'ff'
        xmp_packet = ''
        while True:
            if byte == need_byte:
                need_byte = hex(int(byte, 16) - 1)[2:].rjust(2, '0')
            else:
                xmp_packet += byte
            if need_byte == '00':
                break
            byte = hex_bytes[start:start + 2]
            start += 2
        xmp_packet = xmp_packet
        size_block = start + 30
        return xmp_packet, size_block


class GifInfo:
    def __init__(self, filename=None, qtWindow=None):
        self.images = []
        self.qtWindow = qtWindow
        self.transp_colors = []
        self.frames_info = []
        self.images_trs = []

        self.filename = filename
        self.hexbytes = ''
        if filename:
            self.hexbytes = GifInfo.get_hexbytes(filename)
        self.pointer = 0
        self.lsd = LogicalScreenDescriptor(self.hexbytes)
        self.width = self.lsd.width
        self.height = self.lsd.height
        self.pointer += self.lsd.size_block
        self.gct = ColorTable(self.hexbytes[self.pointer:],
                              self.lsd.is_global_table,
                              self.lsd.size_table)
        self.bg_color = 'ffffff'
        if self.gct.color_table:
            self.bg_color = self.gct.color_table[int(self.lsd.index_bg_color,
                                                     16)]
        self.pointer += self.gct.size_block
        self.extensions = []
        next_block = self.hexbytes[self.pointer:self.pointer + 2]
        self.pointer += 0
        end = False
        self.image_descriptors = []
        self.program_extensions = []
        last_graphic_extension = None
        while not end:
            if qtWindow:
                qtWindow.progress_bar.emit(
                    20 * self.pointer / len(self.hexbytes))
            if next_block == '21':
                extension_bytes = self.hexbytes[self.pointer:]
                extension = GifInfo.process_extension(extension_bytes)
                if isinstance(extension, ProgramExtension):
                    self.program_extensions.append(extension)
                elif isinstance(extension, GraphicExtension):
                    if self.lsd.header == "GIF89a":
                        last_graphic_extension = extension
                    self.extensions.append(extension)
                else:
                    self.extensions.append(extension)
                self.pointer += extension.size_block + 2
            elif next_block == '2c':
                descriptor_bytes = self.hexbytes[self.pointer:]
                self.pointer += 2
                self.last_image_descriptor = ImageDescriptor(descriptor_bytes)
                lid = self.last_image_descriptor
                self.image_descriptors.append(self.last_image_descriptor)
                self.frames_info.append((lid.left,
                                         lid.top,
                                         lid.width,
                                         lid.height))
                self.pointer += self.last_image_descriptor.size_block
                self.last_loc_table = ColorTable(
                    self.hexbytes[self.pointer:],
                    self.last_image_descriptor.is_local_table,
                    self.last_image_descriptor.size_local_table)
                self.pointer += self.last_loc_table.size_block
                if self.pointer > len(self.hexbytes):
                    raise ValueError(EXCEPTION_MESSAGES[8])
                self.graphic_block = GraphicBlock(self.hexbytes[self.pointer:])
                self.last_image_descriptor.graphic_block = self.graphic_block
                transparency_color = None
                if last_graphic_extension:
                    lge = last_graphic_extension
                    self.last_image_descriptor.graphic_extension = lge
                    if lge.transparency_flag == '1':
                        transparency_color = lge.number_transparency_color
                    last_graphic_extension = None
                self.pointer += self.graphic_block.size_block
                need_pal = self.gct.color_table
                self.last_image_descriptor.lct = None
                if self.last_image_descriptor.is_local_table:
                    need_pal = self.last_loc_table.color_table
                    self.last_image_descriptor.lct = self.last_loc_table
                to_append = (GifInfo.decode_lzw(self.graphic_block.subblocks,
                                                self.graphic_block.mc + 1),
                             need_pal,
                             transparency_color)
                self.images.append(to_append)
            elif next_block == '3b':
                end = True
            else:
                raise ValueError(EXCEPTION_MESSAGES[9])
            next_block = self.hexbytes[self.pointer:self.pointer + 2]
            self.pointer += 0
        try:
            self.frames = self.get_all_frames()
        except IndexError:
            raise IndexError('Error: pixels less than it is necessary')

    @staticmethod
    def get_N_subblocks(hex_bytes):
        subblocks = []
        sb_size = int(hex_bytes[2:4], 16)
        sb_start = 4
        while int(hex_bytes[sb_start + sb_size * 2:sb_start + sb_size * 2 + 2],
                  16) != 0:
            subblock = hex_bytes[sb_start:sb_start + 255 * 2]
            subblocks.append(subblock)
            sb_start += sb_size * 2
            sb_size = int(hex_bytes[sb_start:sb_start + 2], 16)
            sb_start += 2
        else:
            subblock = hex_bytes[sb_start:sb_start + sb_size * 2]
            subblocks.append(subblock)
            sb_start += sb_size * 2
        if hex_bytes[sb_start:sb_start + 2] != '00':
            raise ValueError(EXCEPTION_MESSAGES[14])
        sb_start += 2
        size_block = sb_start
        return subblocks, size_block

    @staticmethod
    def process_extension(hex_bytes):
        extension_type = hex_bytes[2:4]
        if extension_type == 'f9':
            return GraphicExtension(hex_bytes[:16])
        elif extension_type == 'ff':
            return ProgramExtension(hex_bytes)
        elif extension_type == 'fe':
            return CommentExtension(hex_bytes[2:])
        else:
            raise ValueError(EXCEPTION_MESSAGES[15])

    def get_all_frames(self):
        frames = [[]]
        image = self.images[0]
        info = [int(e, 16) for e in self.frames_info[0]]
        width = info[2]
        height = info[3]
        pixels_count = width * height
        for i in range(height):
            frames[0].append([])
            for j in range(width):
                frames[0][i].append(image[1][image[0][i * width + j]])
        prev_width = width
        pixel_index = 0
        for i in range(1, len(self.images)):
            frames.append([])
            image = self.images[i]
            info = [int(e, 16) for e in self.frames_info[i]]
            left = info[0]
            top = info[1]
            width = info[2]
            height = info[3]
            frames[i].append([])
            y = 0
            x = 0
            o_i = 0
            for j in range(pixels_count):
                if (x < left or
                        y < top or
                        x >= width + left or
                        y >= height + top):
                    frames[i][y].append(frames[i - 1][y][x])
                else:
                    if (self.bg_color == image[1][image[0][o_i]] or
                            (image[2] and
                             image[1][image[0][o_i]] == image[1][image[2]])):
                        frames[i][y].append(frames[i - 1][y][x])
                    else:
                        frames[i][y].append(image[1][image[0][o_i]])
                    o_i += 1
                x += 1
                if x == prev_width:
                    if j == pixels_count - 1:
                        break
                    frames[i].append([])
                    y += 1
                    x = 0
                pixel_index += 1
            if self.qtWindow:
                self.qtWindow.progress_bar.emit(
                    20 + 10 * pixel_index / (pixels_count * len(self.images)))

        return frames

    @staticmethod
    def swap_pixels(bytes):
        return bytes[-2:] + bytes[:2]

    @staticmethod
    def get_hexbytes(filename):
        with open(filename, 'rb') as f:
            return f.read().hex()

    @staticmethod
    def initialize_lzw_dict(min_len):
        lzw_dict = {}
        end_dict = int(math.pow(2, min_len - 1))
        for i in range(end_dict):
            lzw_dict[i] = [i]
        lzw_dict[end_dict] = 'clear'
        lzw_dict[end_dict + 1] = 'end'
        return lzw_dict

    @staticmethod
    def initialize_lzw(lzw_code, min_len):
        lzw_code = ''.join(lzw_code)
        lzw_dict = {}
        end_dict = int(math.pow(2, min_len - 1))
        for i in range(end_dict):
            lzw_dict[i] = [i]
        lzw_dict[end_dict] = 'clear'
        lzw_dict[end_dict + 1] = 'end'
        end_code = end_dict + 1
        end_dict += 2
        lzw_code_list = []
        for i in range(0, len(lzw_code), 2):
            to_append = bin(int(lzw_code[i:i + 2], 16))[2:].rjust(8, '0')
            lzw_code_list.append(to_append)
        lzw_code_list = lzw_code_list[::-1]
        lzw_code_str = ''.join(lzw_code_list)
        start = len(lzw_code_str)
        if lzw_code_str[start - min_len:start] != bin(end_dict - 2)[2:]:
            sys.exit(1)
        return lzw_dict, lzw_code_str, end_code

    @staticmethod
    def decode_lzw(lzw_code, min_len):
        start_min_len = min_len
        lzw_dict, lzw_code_str, end_code = GifInfo.initialize_lzw(lzw_code,
                                                                  min_len)
        start = len(lzw_code_str) - min_len
        result = []
        previous = int(lzw_code_str[start - min_len:start], 2)
        result.extend(copy.copy(lzw_dict[previous]))
        start -= min_len
        while (int(lzw_code_str[start - min_len:start], 2) != end_code and
               start > min_len):
            input_code = int(lzw_code_str[start - min_len:start], 2)
            if input_code == end_code - 1:
                lzw_dict = GifInfo.initialize_lzw_dict(start_min_len)
                start -= min_len
                min_len = start_min_len
                previous = int(lzw_code_str[start - min_len:start], 2)
                result.extend(copy.copy(lzw_dict[previous]))
                start -= min_len
                continue
            to_add = copy.copy(lzw_dict[previous])
            if input_code in lzw_dict:
                result.extend(lzw_dict[input_code])
                to_add.append(lzw_dict[input_code][0])
            else:
                to_add.append(lzw_dict[previous][0])
                result.extend(to_add)
            lzw_dict[len(lzw_dict)] = copy.copy(to_add)
            previous = input_code
            start -= min_len
            if not (len(lzw_dict) & (len(lzw_dict) - 1)) and min_len < 12:
                min_len += 1
            if start < min_len:
                raise ValueError(EXCEPTION_MESSAGES[16])
        return result
