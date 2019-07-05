import unittest
import os
import sys
from io import StringIO
from GifInfo import *
import cmain


class CmainTest(unittest.TestCase):
    def test_main_errors(self):
        sys.argv[1:] = ['-d', 'raw', 'test_suite/bad/ce77.gif']
        with self.assertRaises(SystemExit):
            cmain.main()
        sys.argv[3] = 'test_suite/bad/9f8f.gif'
        with self.assertRaises(SystemExit):
            cmain.main()
        sys.argv[3] = 'test_suite/bad/f88b.gif'
        with self.assertRaises(SystemExit):
            cmain.main()

    def test_main_create_bmp(self):
        sys.argv[1:] = ['--bmp', ':', 'test_suite/good/10x10.gif']
        self.assertFalse(os.path.exists('test_suite/good/10x10'))
        cmain.main()
        self.assertTrue(os.path.exists('test_suite/good/10x10'))
        self.assertTrue(os.path.isfile('test_suite/good/10x10/1.bmp'))
        self.assertTrue(os.path.isfile('test_suite/good/10x10/2.bmp'))
        os.remove('test_suite/good/10x10/1.bmp')
        os.remove('test_suite/good/10x10/2.bmp')
        os.rmdir('test_suite/good/10x10')

    def test_main_create_bmp_one_frame(self):
        sys.argv[1:] = ['--bmp', '1', 'test_suite/good/10x10.gif']
        self.assertFalse(os.path.exists('test_suite/good/10x10'))
        cmain.main()
        self.assertTrue(os.path.exists('test_suite/good/10x10'))
        self.assertTrue(os.path.isfile('test_suite/good/10x10/1.bmp'))
        os.remove('test_suite/good/10x10/1.bmp')
        os.rmdir('test_suite/good/10x10')

    def test_main_create_bmp_errors(self):
        sys.argv[1:] = ['--bmp', '2:1', 'test_suite/good/10x10.gif']
        with self.assertRaises(SystemExit):
            cmain.main()
        sys.argv[1:] = ['--bmp', '100:150', 'test_suite/good/10x10.gif']
        with self.assertRaises(SystemExit):
            cmain.main()
        sys.argv[1:] = ['--bmp', '11:11:11:11', 'test_suite/good/10x10.gif']
        with self.assertRaises(SystemExit):
            cmain.main()
        sys.argv[1:] = ['--bmp', '100', 'test_suite/good/10x10.gif']
        with self.assertRaises(SystemExit):
            cmain.main()

    def test_main_descr_raw(self):
        sys.argv[1:] = ['test_suite/good/10x10.gif', 'raw_data']
        out = StringIO()
        sys.stdout = out
        cmain.main()
        out = out.getvalue().strip()
        print(out)
        with open('files_for_test/raw') as f:
            expected_result = f.read()
            self.assertEqual(out + '\n', expected_result)

    def test_main_descr_decipher(self):
        sys.argv[1:] = ['test_suite/good/10x10.gif', 'deciphered_data']
        out = StringIO()
        sys.stdout = out
        cmain.main()
        out = out.getvalue().strip()
        with open('files_for_test/decipher') as f:
            expected_result = f.read()
            self.assertEqual(out + '\n', expected_result)

    def test_main_descr_rgb(self):
        sys.argv[1:] = ['test_suite/good/10x10.gif', 'rgb_data']
        out = StringIO()
        sys.stdout = out
        cmain.main()
        out = out.getvalue().strip()
        with open('files_for_test/rgb') as f:
            expected_result = f.read()
            self.assertEqual(out + '\n', expected_result)


class GifInfoTest(unittest.TestCase):
    def test_good_gif(self):
        gif = GifInfo('test_suite/good/e6aa.gif')
        print(gif.hexbytes[:26])
        print(gif)

    def test_gif_with_bad_byte(self):
        with self.assertRaisesRegex(ValueError, EXCEPTION_MESSAGES[9]):
            GifInfo('test_suite/bad/0646.gif')

    def test_gif_with_bad_field_first(self):
        with self.assertRaisesRegex(ValueError, 'Error: wrong field'):
            GifInfo('test_suite/bad/243d.gif')

    def test_gif_with_bad_field_second(self):
        with self.assertRaisesRegex(ValueError, 'size of graphic extension'):
            GifInfo('test_suite/bad/7092.gif')

    def test_gif_with_bad_field_mc_first(self):
        with self.assertRaisesRegex(ValueError, 'Error: wrong field'):
            GifInfo('test_suite/bad/2b5b.gif')

    def test_gif_with_bad_field_mc_second(self):
        with self.assertRaisesRegex(ValueError, 'Error: wrong field'):
            GifInfo('test_suite/bad/5f09.gif')

    def test_gif_with_bad_field_mc_third(self):
        with self.assertRaisesRegex(ValueError, 'Error: wrong field'):
            GifInfo('test_suite/bad/ce77.gif')

    def test_gif_with_undefined_byte(self):
        with self.assertRaisesRegex(ValueError, EXCEPTION_MESSAGES[9]):
            GifInfo('test_suite/bad/adaf.gif')

    def test_gif_with_unexpected_extension(self):
        with self.assertRaises(KeyError):
            GifInfo('test_suite/bad/bc7a.gif')

    def test_gif_with_wrong_header(self):
        with self.assertRaisesRegex(ValueError, EXCEPTION_MESSAGES[4]):
            GifInfo('test_suite/bad/d5a0.gif')

    def test_gif_with_bad_logical_screen_descriptor(self):
        with self.assertRaisesRegex(ValueError, EXCEPTION_MESSAGES[3]):
            GifInfo('test_suite/bad/e341.gif')

    def test_gif_with_bad_graphic_block(self):
        with self.assertRaisesRegex(ValueError, EXCEPTION_MESSAGES[16]):
            GifInfo('test_suite/bad/ea75.gif')

    def test_get_lsd(self):
        hexbytes = '4749463839613c003c00f7fa00'
        lsd = LogicalScreenDescriptor(hexbytes)
        self.assertEqual('003c', lsd.width)
        self.assertEqual('003c', lsd.height)
        self.assertEqual('11110111', lsd.packed_fields)
        self.assertEqual('fa', lsd.index_bg_color)
        self.assertEqual('00', lsd.ratio)

    def test_get_image_descriptor(self):
        hexbytes = '2c000000003c003c0087'
        id = ImageDescriptor(hexbytes)
        self.assertEqual(id.left, '0000')
        self.assertEqual(id.top, '0000')
        self.assertEqual(id.width, '003c')
        self.assertEqual(id.height, '003c')
        self.assertEqual(id.is_local_table, 1)
        self.assertEqual(id.is_interplace, '0')
        self.assertEqual(id.size_local_table, 256)
        self.assertEqual(id.is_sorted_pal, '0')

    def test_bad_logical_image_descriptor(self):
        with self.assertRaisesRegex(ValueError, EXCEPTION_MESSAGES[3]):
            LogicalScreenDescriptor('23156ytrgfd')

    def test_initialize_lzw_dict(self):
        lzw_dict = GifInfo.initialize_lzw_dict(3)
        expected = {0: [0], 1: [1], 2: [2], 3: [3], 4: 'clear', 5: 'end'}
        self.assertEqual(lzw_dict, expected)

    def test_read_xmp_packet(self):
        hexbytes = 'aa32ff454afe54a5fd45a4fc5a45fb45a6fa157f9687123ffab12bf001'
        for i in range(int('f9', 16), 0, -1):
            hexbyte = hex(i)[2:]
            if len(hexbyte) == 1:
                hexbyte = '0' + hexbyte
            hexbytes += hexbyte
        xmp, size = ProgramExtension.read_xmp_packet(hexbytes)
        expected = 'aa32454a54a545a45a4545a6157f9687123ffab12bf001'
        self.assertEqual(xmp, expected)


if __name__ == '__main__':
    unittest.main()
