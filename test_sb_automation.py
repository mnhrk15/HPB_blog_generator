#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from app.blueprints.blog.sb_automation import SalonBoardAutomation, post_to_sb
from flask import Flask
import time

def create_test_app():
    """テスト用のFlaskアプリを作成する"""
    app = Flask(__name__)
    app.config['SELECTORS'] = {
        'sb': {
            'login': {
                'id_selector': '#idPasswordInputForm > div > dl:nth-child(1) > dd > input',
                'password_selector': '#jsiPwInput',
                'login_button_selector': '#idPasswordInputForm > div > div > a'
            },
            'blog': {
                'post_menu_selector': 'a[href*="blog/post"]',
                'title_selector': '#title',
                'stylist_selector': '#stylist',
                'body_selector': '#body',
                'body_frame_selector': 'iframe[id^="body_ifr"]',
                'image_upload_button_selector': '#image_upload',
                'file_input_selector': 'input[type="file"]',
                'insert_image_button_selector': '#insert_image',
                'coupon_selector': '#coupon',
                'publish_option_selector': '#publish_option',
                'post_button_selector': '#post_button',
                'confirm_button_selector': '#confirm_button',
                'success_message_selector': '.success_message'
            }
        }
    }
    return app

def test_login():
    """ログイン機能のテスト"""
    app = create_test_app()
    with app.app_context():
        sb_id = input("サロンボードID: ")
        sb_password = input("サロンボードパスワード: ")
        
        try:
            with SalonBoardAutomation(sb_id, sb_password) as automation:
                print("ブラウザを起動しました")
                print("ログインを試行中...")
                login_success = automation.login()
                if login_success:
                    print("✅ ログイン成功")
                    # スクリーンショットを撮影
                    screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_success.png")
                    automation.page.screenshot(path=screenshot_path)
                    print(f"スクリーンショットを保存しました: {screenshot_path}")
                    
                    # 5秒待機してからブラウザを閉じる
                    time.sleep(5)
                else:
                    print("❌ ログイン失敗")
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

def test_navigate_to_blog_post():
    """ブログ投稿ページへの移動テスト"""
    app = create_test_app()
    with app.app_context():
        sb_id = input("サロンボードID: ")
        sb_password = input("サロンボードパスワード: ")
        
        try:
            with SalonBoardAutomation(sb_id, sb_password) as automation:
                print("ブラウザを起動しました")
                print("ログインを試行中...")
                login_success = automation.login()
                if login_success:
                    print("✅ ログイン成功")
                    
                    print("ブログ投稿ページへの移動を試行中...")
                    navigation_success = automation.navigate_to_blog_post()
                    if navigation_success:
                        print("✅ ブログ投稿ページへの移動成功")
                        # スクリーンショットを撮影
                        screenshot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog_post_page.png")
                        automation.page.screenshot(path=screenshot_path)
                        print(f"スクリーンショットを保存しました: {screenshot_path}")
                        
                        # 5秒待機してからブラウザを閉じる
                        time.sleep(5)
                    else:
                        print("❌ ブログ投稿ページへの移動失敗")
                else:
                    print("❌ ログイン失敗")
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")

def main():
    """メイン関数"""
    print("サロンボード自動化機能テスト")
    print("1. ログインテスト")
    print("2. ブログ投稿ページへの移動テスト")
    choice = input("テスト番号を選択してください: ")
    
    if choice == "1":
        test_login()
    elif choice == "2":
        test_navigate_to_blog_post()
    else:
        print("無効な選択です")

if __name__ == "__main__":
    main()
