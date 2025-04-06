import os
import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
from flask import Flask

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.blueprints.blog.sb_automation import SalonBoardAutomation, post_to_sb
from tests.async_test_case import AsyncTestCase
from app import create_app
from app.config import Config

class TestSalonBoardAutomation(AsyncTestCase):
    """サロンボード自動投稿機能のユニットテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用の一時ディレクトリを作成
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # テスト用のアプリケーションを作成
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'APP_PASSWORD': 'test-password',
            'GEMINI_API_KEY': 'test-api-key',
            'UPLOAD_FOLDER': self.temp_dir.name
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # テスト用の認証情報
        self.test_id = 'test_id'
        self.test_password = 'test_password'
        
        # テスト用のセレクタ設定
        self.test_selectors = {
            'login': {
                'id_selector': '#idPasswordInputForm > div > dl:nth-child(1) > dd > input',
                'password_selector': '#jsiPwInput',
                'login_button_selector': '#idPasswordInputForm > div > div > a'
            },
            'navigation': {
                'publication_button_selector': '.nav-publication',
                'blog_post_button_selector': '.nav-blog'
            },
            'blog': {
                'new_post_button_selector': '.new-post-button',
                'title_selector': '#blog-title',
                'stylist_selector': '#stylist-select',
                'body_selector': '#blog-body',
                'image_upload_button_selector': '.upload-image',
                'file_input_selector': 'input[type="file"]',
                'post_button_selector': '.post-button',
                'success_message_selector': '.success-message'
            }
        }
        
        # テスト用の画像情報
        self.test_images = [
            {
                'filename': 'test1.jpg',
                'path': '/path/to/test1.jpg',
                'placeholder': '[IMAGE_1]'
            }
        ]
    
    def tearDown(self):
        """テストの後処理"""
        # アプリケーションコンテキストをポップ
        self.app_context.pop()
        
        # 一時ディレクトリを削除
        self.temp_dir.cleanup()
    
    @patch('app.blueprints.blog.sb_automation.async_playwright')
    @patch('app.blueprints.blog.sb_automation.current_app')
    async def test_login_success(self, mock_current_app, mock_playwright):
        """ログイン成功のテスト"""
        # モックの設定
        mock_current_app.config.get = MagicMock(return_value=self.test_selectors)
        
        # Playwrightのモック
        mock_page = AsyncMock()
        mock_page.url = 'https://salonboard.com/dashboard'
        
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_chromium
        
        # async_playwright()の返値をモック
        mock_playwright_start = AsyncMock(return_value=mock_playwright_instance)
        mock_playwright.return_value = AsyncMock()
        mock_playwright.return_value.start = mock_playwright_start
        
        # SalonBoardAutomationインスタンスを作成
        automation = SalonBoardAutomation(self.test_id, self.test_password)
        await automation.setup()
        
        # ログイン処理を実行
        result = await automation.login()
        
        # 検証
        self.assertTrue(result)
        mock_page.goto.assert_called_once_with('https://salonboard.com/login/')
        mock_page.fill.assert_any_call(self.test_selectors['login']['id_selector'], self.test_id)
        mock_page.fill.assert_any_call(self.test_selectors['login']['password_selector'], self.test_password)
        mock_page.click.assert_called_once_with(self.test_selectors['login']['login_button_selector'])
    
    @patch('app.blueprints.blog.sb_automation.async_playwright')
    @patch('app.blueprints.blog.sb_automation.current_app')
    async def test_login_failure(self, mock_current_app, mock_playwright):
        """ログイン失敗のテスト"""
        # モックの設定
        mock_current_app.config.get = MagicMock(return_value=self.test_selectors)
        mock_current_app.logger.error = MagicMock()
        
        # Playwrightのモック
        mock_page = AsyncMock()
        mock_page.url = 'https://salonboard.com/login/'  # ログインページのままなのでログイン失敗
        mock_page.inner_text.return_value = 'IDまたはパスワードが間違っています'
        
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_chromium
        
        # async_playwright()の返値をモック
        mock_playwright_start = AsyncMock(return_value=mock_playwright_instance)
        mock_playwright.return_value = AsyncMock()
        mock_playwright.return_value.start = mock_playwright_start
        
        # SalonBoardAutomationインスタンスを作成
        automation = SalonBoardAutomation(self.test_id, self.test_password)
        await automation.setup()
        
        # ログイン処理を実行
        result = await automation.login()
        
        # 検証
        self.assertFalse(result)
        mock_current_app.logger.error.assert_called_once()
    
    @patch('app.blueprints.blog.sb_automation.async_playwright')
    @patch('app.blueprints.blog.sb_automation.current_app')
    async def test_navigate_to_blog_post(self, mock_current_app, mock_playwright):
        """ブログ投稿ページへの移動テスト"""
        # モックの設定
        mock_current_app.config.get = MagicMock(return_value=self.test_selectors)
        
        # Playwrightのモック
        mock_page = AsyncMock()
        
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_chromium
        
        # async_playwright()の返値をモック
        mock_playwright_start = AsyncMock(return_value=mock_playwright_instance)
        mock_playwright.return_value = AsyncMock()
        mock_playwright.return_value.start = mock_playwright_start
        
        # SalonBoardAutomationインスタンスを作成
        automation = SalonBoardAutomation(self.test_id, self.test_password)
        await automation.setup()
        
        # ブログ投稿ページへの移動を実行
        result = await automation.navigate_to_blog_post()
        
        # 検証
        self.assertTrue(result)
        # モックの呼び出しが行われたことを確認
        mock_page.click.assert_called()
    
    @patch('app.blueprints.blog.sb_automation.async_playwright')
    @patch('app.blueprints.blog.sb_automation.current_app')
    async def test_post_blog(self, mock_current_app, mock_playwright):
        """ブログ投稿処理のテスト"""
        # モックの設定
        mock_current_app.config.get = MagicMock(return_value=self.test_selectors)
        
        # Playwrightのモック
        mock_page = AsyncMock()
        mock_page.url = 'https://salonboard.com/blog/list'  # 投稿後のURL
        
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_chromium = AsyncMock()
        mock_chromium.launch.return_value = mock_browser
        
        mock_playwright_instance = AsyncMock()
        mock_playwright_instance.chromium = mock_chromium
        
        # async_playwright()の返値をモック
        mock_playwright_start = AsyncMock(return_value=mock_playwright_instance)
        mock_playwright.return_value = AsyncMock()
        mock_playwright.return_value.start = mock_playwright_start
        
        # SalonBoardAutomationインスタンスを作成
        automation = SalonBoardAutomation(self.test_id, self.test_password)
        await automation.setup()
        
        # ブログ投稿処理を実行
        result = await automation.post_blog(
            title='テストタイトル',
            body='テスト本文 [IMAGE_1]',
            stylist='山田 太郎',
            images=self.test_images,
            coupon='初回限定20%オフ'
        )
        
        # 検証
        self.assertTrue(result)
        # モックの呼び出しが行われたことを確認
        mock_page.fill.assert_called()
        mock_page.click.assert_called()
        mock_page.set_input_files.assert_called_once()
    
    @patch('app.blueprints.blog.sb_automation.SalonBoardAutomation')
    @patch('app.blueprints.blog.sb_automation.current_app')
    async def test_post_to_sb_success(self, mock_current_app, MockSalonBoardAutomation):
        """サロンボード投稿関数の成功テスト"""
        # モックの設定
        mock_current_app.logger.error = MagicMock()
        
        # SalonBoardAutomationのモック
        mock_automation = AsyncMock()
        mock_automation.login = AsyncMock(return_value=True)
        mock_automation.navigate_to_blog_post = AsyncMock(return_value=True)
        mock_automation.post_blog = AsyncMock(return_value=True)
        
        # コンテキストマネージャのモック
        MockSalonBoardAutomation.return_value.__aenter__.return_value = mock_automation
        
        # 関数を実行
        result = await post_to_sb(
            sb_id=self.test_id,
            sb_password=self.test_password,
            title='テストタイトル',
            body='テスト本文',
            stylist='山田 太郎',
            images=self.test_images,
            coupon='初回限定20%オフ'
        )
        
        # 検証
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'ブログが正常に投稿されました。')
        mock_automation.login.assert_called_once()
        mock_automation.navigate_to_blog_post.assert_called_once()
        mock_automation.post_blog.assert_called_once_with(
            'テストタイトル', 'テスト本文', '山田 太郎', self.test_images, '初回限定20%オフ'
        )
    
    @patch('app.blueprints.blog.sb_automation.SalonBoardAutomation')
    @patch('app.blueprints.blog.sb_automation.current_app')
    async def test_post_to_sb_login_failure(self, mock_current_app, MockSalonBoardAutomation):
        """サロンボード投稿関数のログイン失敗テスト"""
        # モックの設定
        mock_current_app.logger.error = MagicMock()
        
        # SalonBoardAutomationのモック
        mock_automation = AsyncMock()
        mock_automation.login = AsyncMock(return_value=False)
        
        # コンテキストマネージャのモック
        MockSalonBoardAutomation.return_value.__aenter__.return_value = mock_automation
        
        # 関数を実行
        result = await post_to_sb(
            sb_id=self.test_id,
            sb_password=self.test_password,
            title='テストタイトル',
            body='テスト本文',
            stylist='山田 太郎',
            images=self.test_images
        )
        
        # 検証
        self.assertFalse(result['success'])
        self.assertIn('ログインに失敗しました', result['message'])
        mock_automation.login.assert_called_once()
        mock_automation.navigate_to_blog_post.assert_not_called()
        mock_automation.post_blog.assert_not_called()

if __name__ == '__main__':
    unittest.main()
