import os
import sys
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.blueprints.blog.scraping import scrape_hpb_data, _scrape_stylists, _scrape_coupons
from tests.async_test_case import AsyncTestCase
from app import create_app

class TestScrapingFunctions(AsyncTestCase):
    """スクレイピング機能のユニットテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # テスト用のアプリケーションを作成
        self.app = create_app({
            'TESTING': True,
            'SECRET_KEY': 'test-secret-key',
            'APP_PASSWORD': 'test-password',
            'UPLOAD_FOLDER': '/tmp/test_uploads'
        })
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # テスト用のURL
        self.test_url = 'https://beauty.hotpepper.jp/slnH000XXXXX'
        
        # テスト用のセレクタ設定
        self.test_selectors = {
            'hpb': {
                'stylist': {
                    'page_url_suffix': 'stylist/',
                    'stylist_name_selector': '.staffList .staffName'
                },
                'coupon': {
                    'page_url_suffix': 'coupon/',
                    'pagination_url_format': 'coupon/PN{n}.html',
                    'coupon_name_selector': '.couponTitle'
                }
            }
        }
        
        # テスト用のHTMLコンテンツ
        self.stylist_html = """
        <html>
        <body>
            <div class="staffList">
                <div class="staffItem">
                    <div class="staffName">山田 太郎</div>
                </div>
                <div class="staffItem">
                    <div class="staffName">佐藤 花子</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        self.coupon_html = """
        <html>
        <body>
            <div class="couponList">
                <div class="couponItem">
                    <div class="couponTitle">初回限定20%オフ</div>
                </div>
                <div class="couponItem">
                    <div class="couponTitle">平日限定クーポン</div>
                </div>
            </div>
            <div class="pagination">
                <ul>
                    <li><a>1</a></li>
                    <li><a>2</a></li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        self.coupon_page2_html = """
        <html>
        <body>
            <div class="couponList">
                <div class="couponItem">
                    <div class="couponTitle">学割クーポン</div>
                </div>
            </div>
        </body>
        </html>
        """
    
    @patch('app.blueprints.blog.scraping.requests.get')
    @patch('app.blueprints.blog.scraping.current_app')
    def test_scrape_stylists(self, mock_current_app, mock_requests_get):
        """スタイリスト情報のスクレイピングテスト"""
        # モックの設定
        mock_current_app.logger.error = MagicMock()
        
        mock_response = MagicMock()
        mock_response.text = self.stylist_html
        mock_response.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_response
        
        # 関数を実行
        result = _scrape_stylists(self.test_url, self.test_selectors)
        
        # 検証
        self.assertEqual(len(result), 2)
        self.assertIn('山田 太郎', result)
        self.assertIn('佐藤 花子', result)
        
        # 実際の関数の動作に合わせて期待するURLを修正
        expected_url = self.test_url + 'stylist/'
        mock_requests_get.assert_called_once_with(
            expected_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
    
    @patch('app.blueprints.blog.scraping.requests.get')
    @patch('app.blueprints.blog.scraping.current_app')
    def test_scrape_stylists_error(self, mock_current_app, mock_requests_get):
        """スタイリスト情報のスクレイピングエラーテスト"""
        # モックの設定
        mock_current_app.logger.error = MagicMock()
        mock_requests_get.side_effect = Exception('Connection error')
        
        # 関数を実行
        result = _scrape_stylists(self.test_url, self.test_selectors)
        
        # 検証
        self.assertEqual(result, [])
        mock_current_app.logger.error.assert_called_once()
    
    @patch('app.blueprints.blog.scraping.requests.get')
    @patch('app.blueprints.blog.scraping.current_app')
    @patch('app.blueprints.blog.scraping.time.sleep')
    def test_scrape_coupons(self, mock_sleep, mock_current_app, mock_requests_get):
        """クーポン情報のスクレイピングテスト"""
        # モックの設定
        mock_current_app.logger.error = MagicMock()
        
        # 1ページ目のレスポンス
        mock_response1 = MagicMock()
        mock_response1.text = self.coupon_html
        mock_response1.raise_for_status = MagicMock()
        
        # 2ページ目のレスポンス
        mock_response2 = MagicMock()
        mock_response2.text = self.coupon_page2_html
        mock_response2.raise_for_status = MagicMock()
        
        # requests.getの戻り値を順番に設定
        mock_requests_get.side_effect = [mock_response1, mock_response2]
        
        # 関数を実行
        result = _scrape_coupons(self.test_url, self.test_selectors)
        
        # 検証
        self.assertEqual(len(result), 3)
        self.assertIn('初回限定20%オフ', result)
        self.assertIn('平日限定クーポン', result)
        self.assertIn('学割クーポン', result)
        self.assertEqual(mock_requests_get.call_count, 2)
        # 2ページ分のデータを取得するため、2回呼び出される
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_any_call(1)  # 過負荷防止の待機
    
    @patch('app.blueprints.blog.scraping._scrape_stylists')
    @patch('app.blueprints.blog.scraping._scrape_coupons')
    @patch('app.blueprints.blog.scraping.current_app')
    def test_scrape_hpb_data(self, mock_current_app, mock_scrape_coupons, mock_scrape_stylists):
        """HPBデータのスクレイピング統合テスト"""
        # モックの設定
        mock_current_app.config.get = MagicMock(return_value=self.test_selectors)
        mock_scrape_stylists.return_value = ['山田 太郎', '佐藤 花子']
        mock_scrape_coupons.return_value = ['初回限定20%オフ', '平日限定クーポン']
        
        # 関数を実行
        result = scrape_hpb_data(self.test_url)
        
        # 検証
        self.assertIn('stylists', result)
        self.assertIn('coupons', result)
        self.assertEqual(len(result['stylists']), 2)
        self.assertEqual(len(result['coupons']), 2)
        mock_scrape_stylists.assert_called_once_with(self.test_url + '/', self.test_selectors)
        mock_scrape_coupons.assert_called_once_with(self.test_url + '/', self.test_selectors)

    def tearDown(self):
        """テストの後処理"""
        # アプリケーションコンテキストをポップ
        self.app_context.pop()

if __name__ == '__main__':
    unittest.main()
