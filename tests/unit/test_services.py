import os
import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.blueprints.blog.services import build_gemini_prompt, generate_blog_with_gemini
from tests.async_test_case import AsyncTestCase
from app import create_app

class TestGeminiServices(AsyncTestCase):
    """Gemini API連携サービスのユニットテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用のアプリケーションを作成
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'APP_PASSWORD': 'test-password',
            'GEMINI_API_KEY': 'test-api-key',
            'UPLOAD_FOLDER': '/tmp/test_uploads'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # テスト用の画像情報
        self.test_images = [
            {
                'filename': 'test1.jpg',
                'path': '/path/to/test1.jpg',
                'placeholder': '[IMAGE_1]'
            },
            {
                'filename': 'test2.jpg',
                'path': '/path/to/test2.jpg',
                'placeholder': '[IMAGE_2]'
            }
        ]
    
    def test_build_gemini_prompt_casual(self):
        """カジュアル文体でのプロンプト生成テスト"""
        # 関数を実行
        prompt = build_gemini_prompt(self.test_images, 'casual', 'https://example.com')
        
        # 検証
        self.assertIn('親しみやすいカジュアルな文体で書いてください', prompt)
        self.assertIn('2枚の画像を適切な位置に配置してください', prompt)
        self.assertIn('店舗URL: https://example.com', prompt)
    
    def test_build_gemini_prompt_formal(self):
        """フォーマル文体でのプロンプト生成テスト"""
        # 関数を実行
        prompt = build_gemini_prompt(self.test_images, 'formal')
        
        # 検証
        self.assertIn('丁寧でフォーマルな文体で書いてください', prompt)
        self.assertIn('2枚の画像を適切な位置に配置してください', prompt)
        self.assertNotIn('店舗URL', prompt)  # URLなしの場合
    
    @patch('app.blueprints.blog.services.genai')
    @patch('app.blueprints.blog.services.current_app')
    @patch('app.blueprints.blog.services.open', create=True)
    async def test_generate_blog_with_gemini_success(self, mock_open, mock_current_app, mock_genai):
        """Gemini APIによるブログ生成成功のテスト"""
        # モックの設定
        mock_config = MagicMock()
        mock_config.get.return_value = 'test_api_key'
        mock_current_app.config = mock_config
        mock_genai.GenerativeModel.return_value.generate_content_async = AsyncMock()
        
        # レスポンスのモック
        mock_response = MagicMock()
        mock_response.text = '{"title": "テストタイトル", "body": "テスト本文"}'
        mock_genai.GenerativeModel.return_value.generate_content_async.return_value = mock_response
        
        # ファイルオープンのモック
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = b'test_image_data'
        mock_open.return_value = mock_file
        
        # 関数を実行
        result = await generate_blog_with_gemini(self.test_images, 'casual', 'https://example.com')
        
        # 検証
        self.assertEqual(result['title'], 'テストタイトル')
        self.assertEqual(result['body'], 'テスト本文')
        mock_genai.configure.assert_called_once_with(api_key='test_api_key')
    
    @patch('app.blueprints.blog.services.genai')
    @patch('app.blueprints.blog.services.current_app')
    @patch('app.blueprints.blog.services.open', create=True)
    async def test_generate_blog_with_gemini_error(self, mock_open, mock_current_app, mock_genai):
        """Gemini API呼び出しエラーのテスト"""
        # モックの設定
        mock_config = MagicMock()
        mock_config.get.return_value = 'test_api_key'
        mock_current_app.config = mock_config
        mock_current_app.logger.error = MagicMock()
        mock_genai.GenerativeModel.return_value.generate_content_async = AsyncMock(side_effect=Exception('API error'))
        
        # ファイルオープンのモック
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = b'test_image_data'
        mock_open.return_value = mock_file
        
        # 関数を実行
        result = await generate_blog_with_gemini(self.test_images, 'casual')
        
        # 検証
        self.assertEqual(result['title'], 'エラーが発生しました')
        self.assertIn('ブログの生成中にエラーが発生しました', result['body'])
        mock_current_app.logger.error.assert_called_once()

    def tearDown(self):
        """テストの後処理"""
        # アプリケーションコンテキストをポップ
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()
