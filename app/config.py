import os
import json
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

class Config:
    """アプリケーション設定クラス"""
    
    # Flaskの基本設定
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev_key_please_change')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # アプリケーション共通パスワード
    APP_PASSWORD = os.getenv('APP_PASSWORD', 'password')
    
    # Gemini API設定
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # 一時ファイル保存ディレクトリ
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_uploads')
    
    # セレクタ設定
    SELECTORS = {}
    
    # セレクタ設定の読み込み
    @staticmethod
    def get_selectors():
        """selectors.jsonからセレクタ設定を読み込む"""
        selector_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'selectors.json')
        try:
            with open(selector_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"セレクタ設定の読み込みに失敗しました: {e}")
            return {}
