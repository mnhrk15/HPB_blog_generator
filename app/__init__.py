import os
from flask import Flask

def create_app(test_config=None):
    """Flaskアプリケーションファクトリ関数"""
    
    # アプリケーションの作成と設定
    app = Flask(__name__, instance_relative_config=True)
    
    # 設定の読み込み
    if test_config is None:
        # テスト設定がない場合は、config.pyから設定を読み込む
        from .config import Config
        config = Config()
        app.config.from_object(config)
        
        # selectors.jsonからセレクタ設定を読み込む
        import json
        import os
        selector_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'selectors.json')
        try:
            with open(selector_path, 'r', encoding='utf-8') as f:
                app.config['SELECTORS'] = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            app.logger.error(f"セレクタ設定の読み込みに失敗しました: {e}")
            app.config['SELECTORS'] = {}
    else:
        # テスト設定がある場合は、それを適用
        # 辞書の場合はfrom_mapping、オブジェクトの場合はfrom_objectを使用
        if isinstance(test_config, dict):
            app.config.from_mapping(test_config)
        else:
            app.config.from_object(test_config)
    
    # アップロードフォルダの作成（存在しない場合）
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # ルートルートの設定
    @app.route('/hello')
    def hello():
        return 'Hello, HPB Blog Generator!'
    
    # 認証Blueprintの登録
    from .blueprints.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    # ブログBlueprintの登録
    from .blueprints.blog import bp as blog_bp
    app.register_blueprint(blog_bp)
    
    return app
