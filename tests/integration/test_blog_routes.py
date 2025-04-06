import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import io
from flask import session

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.config import Config

class TestConfig(Config):
    """テスト用の設定クラス"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    APP_PASSWORD = 'test-password'
    GEMINI_API_KEY = 'test-api-key'

class TestBlogRoutes(unittest.TestCase):
    """ブログ機能のルートの統合テスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用のアプリケーションを作成
        self.app = create_app(TestConfig())
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # テスト用の一時ディレクトリを作成
        self.temp_dir = tempfile.TemporaryDirectory()
        self.app.config['UPLOAD_FOLDER'] = self.temp_dir.name
        
        # テスト用の画像データを作成（最小限のJPEG）
        self.test_image_data = (
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
        
        # ログイン状態を作る
        with self.client.session_transaction() as sess:
            sess['logged_in'] = True
    
    def tearDown(self):
        """テストの後処理"""
        # 一時ディレクトリを削除
        self.temp_dir.cleanup()
        
        # アプリケーションコンテキストをポップ
        self.app_context.pop()
    
    def test_index_redirect(self):
        """インデックスページのリダイレクトテスト"""
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/blog/create' in response.location)
    
    def test_create_get(self):
        """ブログ作成ページのGETリクエストテスト"""
        response = self.client.get('/blog/create')
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h2>ブログ作成</h2>'.encode('utf-8'), response.data)
        self.assertIn(b'<form method="post" enctype="multipart/form-data"', response.data)
    
    @patch('app.blueprints.blog.routes.save_uploaded_image')
    def test_create_post_success(self, mock_save_uploaded_image):
        """ブログ作成ページのPOSTリクエスト成功テスト"""
        # モックの設定
        mock_save_uploaded_image.return_value = {
            'filename': 'test_image.jpg',
            'path': os.path.join(self.temp_dir.name, 'test_image.jpg')
        }
        
        # テスト用の画像ファイルを作成
        test_file = (io.BytesIO(self.test_image_data), 'test.jpg')
        
        # POSTリクエストを送信
        response = self.client.post(
            '/blog/create',
            data={
                'store_url': 'https://beauty.hotpepper.jp/slnH000XXXXX/',
                'template_text': 'テストテンプレート',
                'style': 'casual',
                'images': test_file
            },
            content_type='multipart/form-data',
            follow_redirects=False
        )
        
        # 検証
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/blog/generate' in response.location)
        
        # セッションの検証
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['store_url'], 'https://beauty.hotpepper.jp/slnH000XXXXX/')
            self.assertEqual(sess['template_text'], 'テストテンプレート')
            self.assertEqual(sess['style'], 'casual')
            self.assertIn('uploaded_images', sess)
    
    def test_create_post_missing_url(self):
        """ブログ作成ページのPOSTリクエスト（URL欠落）テスト"""
        # テスト用の画像ファイルを作成
        test_file = (io.BytesIO(self.test_image_data), 'test.jpg')
        
        # POSTリクエストを送信
        response = self.client.post(
            '/blog/create',
            data={
                'store_url': '',  # URLを空にする
                'template_text': 'テストテンプレート',
                'style': 'casual',
                'images': test_file
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # 検証
        self.assertEqual(response.status_code, 200)
        self.assertIn('HPB店舗URLを入力してください'.encode('utf-8'), response.data)
    
    def test_create_post_missing_images(self):
        """ブログ作成ページのPOSTリクエスト（画像欠落）テスト"""
        # POSTリクエストを送信
        response = self.client.post(
            '/blog/create',
            data={
                'store_url': 'https://beauty.hotpepper.jp/slnH000XXXXX/',
                'template_text': 'テストテンプレート',
                'style': 'casual',
                # 画像を指定しない
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # 検証
        self.assertEqual(response.status_code, 200)
        self.assertIn('少なくとも1枚の画像をアップロードしてください'.encode('utf-8'), response.data)
    
    @patch('app.blueprints.blog.routes.scrape_hpb_data')
    @patch('app.blueprints.blog.routes.generate_blog_with_gemini')
    @patch('app.blueprints.blog.routes.asyncio')
    def test_generate(self, mock_asyncio, mock_generate_blog, mock_scrape_hpb):
        """ブログ生成処理のテスト"""
        # モックの設定
        mock_scrape_hpb.return_value = {
            'stylists': ['山田 太郎', '佐藤 花子'],
            'coupons': ['初回限定20%オフ', '平日限定クーポン']
        }
        
        mock_generate_blog_result = {
            'title': 'テストタイトル',
            'body': 'テスト本文 [IMAGE_1]'
        }
        mock_loop = MagicMock()
        mock_loop.run_until_complete.return_value = mock_generate_blog_result
        mock_asyncio.new_event_loop.return_value = mock_loop
        
        # セッションにデータを設定
        with self.client.session_transaction() as sess:
            sess['store_url'] = 'https://beauty.hotpepper.jp/slnH000XXXXX/'
            sess['template_text'] = 'テストテンプレート'
            sess['style'] = 'casual'
            sess['uploaded_images'] = [{
                'filename': 'test_image.jpg',
                'path': os.path.join(self.temp_dir.name, 'test_image.jpg'),
                'placeholder': '[IMAGE_1]'
            }]
        
        # GETリクエストを送信
        response = self.client.get('/blog/generate', follow_redirects=False)
        
        # 検証
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/blog/edit' in response.location)
        
        # セッションの検証
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['scraped_data'], mock_scrape_hpb.return_value)
            self.assertEqual(sess['generated_data']['title'], 'テストタイトル')
            self.assertIn('テスト本文', sess['generated_data']['body'])
            self.assertIn('テストテンプレート', sess['generated_data']['body'])
    
    def test_edit(self):
        """編集・確認画面のテスト"""
        # セッションにデータを設定
        with self.client.session_transaction() as sess:
            sess['store_url'] = 'https://beauty.hotpepper.jp/slnH000XXXXX/'
            sess['uploaded_images'] = [{
                'filename': 'test_image.jpg',
                'path': os.path.join(self.temp_dir.name, 'test_image.jpg'),
                'placeholder': '[IMAGE_1]'
            }]
            sess['generated_data'] = {
                'title': 'テストタイトル',
                'body': 'テスト本文 [IMAGE_1]'
            }
            sess['scraped_data'] = {
                'stylists': ['山田 太郎', '佐藤 花子'],
                'coupons': ['初回限定20%オフ', '平日限定クーポン']
            }
        
        # GETリクエストを送信
        response = self.client.get('/blog/edit')
        
        # 検証
        self.assertEqual(response.status_code, 200)
        self.assertIn('<h2>ブログ編集・確認</h2>'.encode('utf-8'), response.data)
        self.assertIn('テストタイトル'.encode('utf-8'), response.data)
        self.assertIn('テスト本文'.encode('utf-8'), response.data)
        self.assertIn('山田 太郎'.encode('utf-8'), response.data)
        self.assertIn('初回限定20%オフ'.encode('utf-8'), response.data)
    
    @patch('app.blueprints.blog.routes.post_to_sb')
    @patch('app.blueprints.blog.routes.clean_session_images')
    @patch('app.blueprints.blog.routes.asyncio')
    def test_post_to_sb_success(self, mock_asyncio, mock_clean_session, mock_post_to_sb):
        """サロンボード投稿処理の成功テスト"""
        # モックの設定
        mock_post_to_sb_result = {
            'success': True,
            'message': 'ブログが正常に投稿されました。'
        }
        mock_loop = MagicMock()
        mock_loop.run_until_complete.return_value = mock_post_to_sb_result
        mock_asyncio.new_event_loop.return_value = mock_loop
        
        # セッションにデータを設定
        with self.client.session_transaction() as sess:
            sess['uploaded_images'] = [{
                'filename': 'test_image.jpg',
                'path': os.path.join(self.temp_dir.name, 'test_image.jpg'),
                'placeholder': '[IMAGE_1]'
            }]
        
        # POSTリクエストを送信
        response = self.client.post(
            '/blog/post_to_sb',
            data={
                'sb_id': 'test_id',
                'sb_password': 'test_password',
                'title': 'テストタイトル',
                'body': 'テスト本文 [IMAGE_1]',
                'stylist': '山田 太郎',
                'coupon': '初回限定20%オフ'
            },
            follow_redirects=False
        )
        
        # 検証
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/blog/create' in response.location)
        mock_clean_session.assert_called_once()
    
    @patch('app.blueprints.blog.routes.post_to_sb')
    @patch('app.blueprints.blog.routes.asyncio')
    def test_post_to_sb_failure(self, mock_asyncio, mock_post_to_sb):
        """サロンボード投稿処理の失敗テスト"""
        # モックの設定
        mock_post_to_sb_result = {
            'success': False,
            'message': 'ログインに失敗しました。'
        }
        mock_loop = MagicMock()
        mock_loop.run_until_complete.return_value = mock_post_to_sb_result
        mock_asyncio.new_event_loop.return_value = mock_loop
        
        # セッションにデータを設定
        with self.client.session_transaction() as sess:
            sess['uploaded_images'] = [{
                'filename': 'test_image.jpg',
                'path': os.path.join(self.temp_dir.name, 'test_image.jpg'),
                'placeholder': '[IMAGE_1]'
            }]
        
        # POSTリクエストを送信
        response = self.client.post(
            '/blog/post_to_sb',
            data={
                'sb_id': 'test_id',
                'sb_password': 'test_password',
                'title': 'テストタイトル',
                'body': 'テスト本文 [IMAGE_1]',
                'stylist': '山田 太郎'
            },
            follow_redirects=True
        )
        
        # 検証
        self.assertEqual(response.status_code, 200)
        self.assertIn('投稿に失敗しました'.encode('utf-8'), response.data)

if __name__ == '__main__':
    unittest.main()
