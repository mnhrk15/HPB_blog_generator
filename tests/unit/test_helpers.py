import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
from werkzeug.datastructures import FileStorage
from io import BytesIO
from flask import Flask

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.helpers import is_valid_image, save_uploaded_image, clean_session_images
from app import create_app

class TestHelperFunctions(unittest.TestCase):
    """ヘルパー関数のユニットテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # テスト用のアプリケーションを作成
        self.app = create_app({
            'TESTING': True,
            'UPLOAD_FOLDER': self.temp_dir.name
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # テスト用の画像データを作成（最小限のJPEG）
        self.valid_jpeg_data = (
            b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06'
            b'\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a'
            b'\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c'
            b'\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11'
            b'\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01'
            b'\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b'
            b'\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03'
            b'\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82'
            b'\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88'
            b'\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4'
            b'\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9'
            b'\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4'
            b'\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03'
            b'\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04'
            b'\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1'
            b'\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghij'
            b'stuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4'
            b'\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9'
            b'\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5'
            b'\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00'
            b'\xff\xd9'
        )
        
        # 無効な画像データ
        self.invalid_image_data = b'not an image'
    
    def tearDown(self):
        """テストの後処理"""
        # アプリケーションコンテキストをポップ
        self.app_context.pop()
        
        # 一時ディレクトリを削除
        self.temp_dir.cleanup()
    
    def test_is_valid_image_with_valid_jpeg(self):
        """有効なJPEG画像の検証テスト"""
        # テスト用のFileStorageオブジェクトを作成
        file = FileStorage(
            stream=BytesIO(self.valid_jpeg_data),
            filename='test.jpg',
            content_type='image/jpeg'
        )
        
        # 検証
        self.assertTrue(is_valid_image(file))
    
    def test_is_valid_image_with_invalid_file(self):
        """無効なファイルの検証テスト"""
        # テスト用のFileStorageオブジェクトを作成
        file = FileStorage(
            stream=BytesIO(self.invalid_image_data),
            filename='test.txt',
            content_type='text/plain'
        )
        
        # 検証
        self.assertFalse(is_valid_image(file))
    
    def test_save_uploaded_image(self):
        """画像保存機能のテスト"""
        # テスト用の一時ディレクトリを作成
        with tempfile.TemporaryDirectory() as temp_dir:
            # アプリケーションの設定を一時的に上書き
            self.app.config['UPLOAD_FOLDER'] = temp_dir
        
            # テスト用のFileStorageオブジェクトを作成
            file = FileStorage(
                stream=BytesIO(self.valid_jpeg_data),
                filename='test.jpg',
                content_type='image/jpeg'
            )
            
            # 関数を実行
            result = save_uploaded_image(file)
            
            # 検証
            self.assertIn('filename', result)
            self.assertIn('path', result)
            self.assertIn('original_filename', result)
            self.assertTrue(os.path.exists(result['path']), f"File {result['path']} does not exist")
            # ファイル名は UUID + 拡張子の形式
            self.assertTrue(result['filename'].endswith('.jpg'))
            self.assertEqual(result['original_filename'], 'test.jpg')
    
    @patch('app.utils.helpers.os.path.exists')
    @patch('app.utils.helpers.os.remove')
    def test_clean_session_images(self, mock_remove, mock_exists):
        """セッション画像のクリーンアップテスト"""
        # モックの設定
        mock_exists.return_value = True
        
        # テスト用の画像情報
        images = [
            {'path': '/path/to/image1.jpg'},
            {'path': '/path/to/image2.jpg'}
        ]
        
        # 関数を実行
        clean_session_images(images)
        
        # 検証
        self.assertEqual(mock_remove.call_count, 2)
        mock_remove.assert_any_call('/path/to/image1.jpg')
        mock_remove.assert_any_call('/path/to/image2.jpg')

if __name__ == '__main__':
    unittest.main()
