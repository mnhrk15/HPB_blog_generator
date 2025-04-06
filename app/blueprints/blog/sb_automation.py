import os
import time
from typing import Dict, List, Optional
from flask import current_app
from playwright.sync_api import sync_playwright
import re

class SalonBoardAutomation:
    """サロンボード自動投稿を行うクラス"""
    
    def __init__(self, sb_id: str, sb_password: str):
        """初期化
        
        Args:
            sb_id: サロンボードID
            sb_password: サロンボードパスワード
        """
        self.sb_id = sb_id
        self.sb_password = sb_password
        selectors = current_app.config.get('SELECTORS', {})
        self.selectors = selectors.get('sb', {})
        self.login_url = "https://salonboard.com/login/"
        self.browser = None
        self.page = None
        self.playwright = None
    
    def __enter__(self):
        """コンテキストマネージャの開始"""
        self.setup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャの終了"""
        self.teardown()
    
    def setup(self):
        """ブラウザとページのセットアップ"""
        try:
            self.playwright = sync_playwright().start()
            # macOSでの安定性向上のためのオプションを追加
            self.browser = self.playwright.chromium.launch(
                headless=False,
                slow_mo=50,  # 操作間の遅延を追加して安定性を向上
                args=[
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-gpu',
                    '--disable-web-security'
                ],
                timeout=30000  # 30秒のタイムアウト
            )
            # コンテキストを作成
            context = self.browser.new_context(viewport={"width": 1280, "height": 800})
            self.page = context.new_page()
        except Exception as e:
            current_app.logger.error(f"ブラウザセットアップエラー: {str(e)}")
            self.teardown()
            raise
    
    def teardown(self):
        """ブラウザとページのクリーンアップ"""
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
        except Exception as e:
            current_app.logger.error(f"ブラウザ終了エラー: {str(e)}")
    
    def login(self) -> bool:
        """サロンボードにログインする
        
        Returns:
            bool: ログイン成功したかどうか
        """
        try:
            # ログインページに移動
            self.page.goto(self.login_url, timeout=30000)
            
            # ID入力
            id_selector = self.selectors.get('login', {}).get('id_selector', '#idPasswordInputForm > div > dl:nth-child(1) > dd > input')
            self.page.fill(id_selector, self.sb_id)
            
            # パスワード入力
            password_selector = self.selectors.get('login', {}).get('password_selector', '#jsiPwInput')
            self.page.fill(password_selector, self.sb_password)
            
            # ログインボタンクリック
            login_button_selector = self.selectors.get('login', {}).get('login_button_selector', '#idPasswordInputForm > div > div > a')
            self.page.click(login_button_selector)
            
            # ログイン成功の確認（ダッシュボードに遷移したか）
            self.page.wait_for_load_state('networkidle', timeout=30000)
            
            # URLがダッシュボードに変わったか、またはログイン成功要素があるか確認
            current_url = self.page.url
            if "dashboard" in current_url or "top" in current_url:
                return True
            
            # ログイン失敗の場合
            try:
                error_message = self.page.inner_text('.error-message')
                if error_message:
                    current_app.logger.error(f"ログインエラー: {error_message}")
            except Exception:
                pass
            
            return False
        
        except Exception as e:
            current_app.logger.error(f"ログイン処理エラー: {str(e)}")
            return False
    
    async def navigate_to_blog_post(self) -> bool:
        """ブログ投稿ページに移動する
        
        Returns:
            bool: 移動成功したかどうか
        """
        try:
            # 掲載管理ボタンをクリック
            publication_button_selector = self.selectors.get('navigation', {}).get('publication_button_selector')
            await self.page.click(publication_button_selector)
            await self.page.wait_for_load_state('networkidle')
            
            # ブログ投稿ボタンをクリック
            blog_post_button_selector = self.selectors.get('navigation', {}).get('blog_post_button_selector')
            await self.page.click(blog_post_button_selector)
            await self.page.wait_for_load_state('networkidle')
            
            # 新規投稿ボタンをクリック
            new_post_button_selector = self.selectors.get('blog', {}).get('new_post_button_selector')
            await self.page.click(new_post_button_selector)
            await self.page.wait_for_load_state('networkidle')
            
            return True
        
        except Exception as e:
            current_app.logger.error(f"ブログ投稿ページへの移動エラー: {str(e)}")
            return False
    
    def post_blog(self, title: str, body: str, stylist: str, images: List[Dict], coupon: Optional[str] = None) -> bool:
        """ブログを投稿する
        
        Args:
            title: ブログタイトル
            body: ブログ本文
            stylist: 投稿スタイリスト
            images: 画像情報のリスト
            coupon: クーポン（任意）
            
        Returns:
            bool: 投稿成功したかどうか
        """
        try:
            # タイトル入力
            title_selector = self.selectors.get('blog', {}).get('title_selector')
            self.page.fill(title_selector, title)
            
            # スタイリスト選択
            stylist_selector = self.selectors.get('blog', {}).get('stylist_selector')
            self.page.select_option(stylist_selector, label=stylist)
            
            # 本文の処理（画像プレースホルダーを実際の画像に置き換え）
            processed_body = body
            
            # 本文入力
            body_selector = self.selectors.get('blog', {}).get('body_selector')
            
            # フレームがある場合はフレームに切り替え
            frame_selector = self.selectors.get('blog', {}).get('body_frame_selector')
            if frame_selector:
                frame = self.page.frame_locator(frame_selector).first
                frame.fill('body', processed_body)
            else:
                self.page.fill(body_selector, processed_body)
            
            # 画像アップロード
            for img_info in images:
                # 画像アップロードボタンをクリック
                image_upload_button_selector = self.selectors.get('blog', {}).get('image_upload_button_selector')
                self.page.click(image_upload_button_selector)
                
                # ファイル選択ダイアログが表示されるのを待つ
                file_input_selector = self.selectors.get('blog', {}).get('file_input_selector')
                self.page.set_input_files(file_input_selector, img_info['path'])
                
                # アップロード完了を待つ
                self.page.wait_for_load_state('networkidle')
                
                # 必要に応じて「挿入」ボタンをクリック
                insert_button_selector = self.selectors.get('blog', {}).get('insert_image_button_selector')
                if insert_button_selector:
                    self.page.click(insert_button_selector)
            
            # クーポン選択（指定がある場合）
            if coupon:
                coupon_selector = self.selectors.get('blog', {}).get('coupon_selector')
                self.page.select_option(coupon_selector, label=coupon)
            
            # 公開設定
            publish_option_selector = self.selectors.get('blog', {}).get('publish_option_selector')
            self.page.click(publish_option_selector)
            
            # 投稿ボタンクリック
            post_button_selector = self.selectors.get('blog', {}).get('post_button_selector')
            self.page.click(post_button_selector)
            
            # 確認ダイアログがある場合は「OK」をクリック
            confirm_button_selector = self.selectors.get('blog', {}).get('confirm_button_selector')
            if confirm_button_selector:
                self.page.click(confirm_button_selector)
            
            # 投稿完了を待つ
            self.page.wait_for_load_state('networkidle')
            
            # 投稿成功の確認
            success_message_selector = self.selectors.get('blog', {}).get('success_message_selector')
            if success_message_selector:
                success_message = self.page.inner_text(success_message_selector)
                if "完了" in success_message or "成功" in success_message:
                    return True
            
            # 投稿一覧ページに戻っていれば成功とみなす
            current_url = self.page.url
            if "blog/list" in current_url or "blog_list" in current_url:
                return True
            
            return False
        
        except Exception as e:
            current_app.logger.error(f"ブログ投稿処理エラー: {str(e)}")
            return False

def post_to_sb(sb_id: str, sb_password: str, title: str, body: str, stylist: str, 
                    images: List[Dict], coupon: Optional[str] = None) -> Dict:
    """サロンボードにブログを投稿する
    
    Args:
        sb_id: サロンボードID
        sb_password: サロンボードパスワード
        title: ブログタイトル
        body: ブログ本文
        stylist: 投稿スタイリスト
        images: 画像情報のリスト
        coupon: クーポン（任意）
        
    Returns:
        Dict: 投稿結果
    """
    try:
        with SalonBoardAutomation(sb_id, sb_password) as automation:
            # ログイン
            login_success = automation.login()
            if not login_success:
                return {
                    'success': False,
                    'message': 'ログインに失敗しました。IDとパスワードを確認してください。'
                }
            
            # ブログ投稿ページに移動
            navigation_success = automation.navigate_to_blog_post()
            if not navigation_success:
                return {
                    'success': False,
                    'message': 'ブログ投稿ページへの移動に失敗しました。'
                }
            
            # ブログ投稿
            post_success = automation.post_blog(title, body, stylist, images, coupon)
            if not post_success:
                return {
                    'success': False,
                    'message': 'ブログの投稿に失敗しました。'
                }
            
            return {
                'success': True,
                'message': 'ブログが正常に投稿されました。'
            }
    
    except Exception as e:
        current_app.logger.error(f"サロンボード投稿エラー: {str(e)}")
        return {
            'success': False,
            'message': f'エラーが発生しました: {str(e)}'
        }
