import os
import sys
import json
from flask import Flask
from app.blueprints.blog.scraping import scrape_hpb_data

def create_test_app():
    """テスト用のFlaskアプリケーションを作成"""
    app = Flask(__name__)
    
    # セレクタ設定の読み込み
    selector_path = os.path.join(os.path.dirname(__file__), 'selectors.json')
    try:
        with open(selector_path, 'r', encoding='utf-8') as f:
            app.config['SELECTORS'] = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"セレクタ設定の読み込みに失敗しました: {e}")
        app.config['SELECTORS'] = {}
    
    return app

def test_scraping(url):
    """スクレイピング機能のテスト"""
    app = create_test_app()
    
    with app.app_context():
        print(f"URL: {url} のスクレイピングを開始します...")
        
        try:
            # スクレイピング実行
            result = scrape_hpb_data(url)
            
            # 結果の表示
            print("\n=== スクレイピング結果 ===")
            print(f"スタイリスト数: {len(result['stylists'])}")
            print("スタイリスト一覧:")
            for i, stylist in enumerate(result['stylists'], 1):
                print(f"  {i}. {stylist}")
            
            print(f"\nクーポン数: {len(result['coupons'])}")
            print("クーポン一覧:")
            for i, coupon in enumerate(result['coupons'], 1):
                print(f"  {i}. {coupon}")
            
            return result
        except Exception as e:
            print(f"スクレイピングエラー: {e}")
            return None

if __name__ == "__main__":
    # コマンドライン引数からURLを取得、なければデフォルトURLを使用
    url = sys.argv[1] if len(sys.argv) > 1 else "https://beauty.hotpepper.jp/slnH000492277/"
    test_scraping(url)
