import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

def save_uploaded_image(file, upload_folder=None):
    """アップロードされた画像を一時ディレクトリに保存する

    Args:
        file: FileStorage オブジェクト
        upload_folder: 保存先ディレクトリ（指定がなければconfigから取得）

    Returns:
        dict: 保存された画像の情報（filename, original_filename, path, placeholder）
    """
    if upload_folder is None:
        upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # ディレクトリが存在しない場合は作成
    os.makedirs(upload_folder, exist_ok=True)
    
    # オリジナルのファイル名を保存
    original_filename = secure_filename(file.filename)
    
    # 一意のファイル名を生成（UUID + オリジナルの拡張子）
    ext = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    # ファイルパスを作成
    file_path = os.path.join(upload_folder, unique_filename)
    
    # ファイルを保存
    file.save(file_path)
    
    # プレースホルダー名を生成（[IMAGE_N]形式）
    # 実際のインデックスは呼び出し元で設定する必要がある
    placeholder = "[IMAGE_1]"
    
    return {
        'filename': unique_filename,
        'original_filename': original_filename,
        'path': file_path,
        'placeholder': placeholder
    }

def delete_temp_file(file_path):
    """一時ファイルを削除する

    Args:
        file_path: 削除するファイルのパス
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"ファイル削除エラー: {e}")
    return False

def is_valid_image(file):
    """有効な画像ファイルかどうかを検証する

    Args:
        file: FileStorage オブジェクト

    Returns:
        bool: 有効な画像の場合はTrue
    """
    # MIMEタイプをチェック
    allowed_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
    return file.content_type in allowed_types

def clean_session_images(session_images, upload_folder=None):
    """セッションに保存されている画像の一時ファイルを削除する

    Args:
        session_images: セッションに保存されている画像情報のリスト
        upload_folder: 一時ファイルディレクトリ
    """
    if not session_images:
        return
    
    for img in session_images:
        if 'path' in img:
            delete_temp_file(img['path'])
