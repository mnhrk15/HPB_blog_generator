import os
import google.generativeai as genai
from flask import current_app
from typing import List, Dict, Optional

def setup_gemini_api():
    """Gemini APIの初期設定を行う"""
    api_key = current_app.config.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEYが設定されていません。.envファイルを確認してください。")
    
    genai.configure(api_key=api_key)

def build_gemini_prompt(images: List[Dict], style: str, store_url: Optional[str] = None) -> str:
    """Gemini APIに送信するプロンプトを生成する
    
    Args:
        images: 画像情報のリスト
        style: 文体スタイル
        store_url: HPB店舗URL（任意）
        
    Returns:
        str: 生成されたプロンプト
    """
    # 文体スタイルに応じたプロンプト調整
    style_instructions = {
        'casual': '親しみやすいカジュアルな文体で書いてください。',
        'formal': '丁寧でフォーマルな文体で書いてください。',
        'professional': '美容のプロフェッショナルとしての専門的な文体で書いてください。',
        'trendy': '若者向けのトレンディな言葉遣いで書いてください。'
    }
    
    style_instruction = style_instructions.get(style, style_instructions['casual'])
    
    # 画像の数に応じたプロンプト調整
    image_count = len(images)
    image_instruction = f"{image_count}枚の画像を適切な位置に配置してください。画像の挿入位置は[IMAGE_1], [IMAGE_2]のように指定してください。"
    
    # プロンプトの構築
    prompt = f"""
あなたは美容室のブログ記事を作成するプロフェッショナルです。
以下の画像を使用して、美容室のブログ記事を作成してください。

【指示】
1. 画像の内容を詳しく分析し、ヘアスタイル、カラー、カット、パーマなどの特徴を詳細に説明してください。
2. タイトルと本文を作成してください。
3. {style_instruction}
4. {image_instruction}
5. 記事の長さは300〜500文字程度にしてください。
6. 記事の構成は以下の通りにしてください：
   - 魅力的なタイトル
   - スタイルの特徴や魅力の説明
   - おすすめの人や似合う顔型
   - スタイリング方法や維持のコツ
   - まとめや来店を促す一言

【出力形式】
以下のJSON形式で出力してください：
{{
  "title": "ブログタイトル",
  "body": "ブログ本文（[IMAGE_N]のプレースホルダーを含む）"
}}

【注意点】
- 専門的な美容用語を適切に使用してください。
- 顧客が来店したくなるような魅力的な表現を使ってください。
- 画像に写っている内容を具体的に説明してください。
"""
    
    if store_url:
        prompt += f"\n- 店舗URL: {store_url}"
    
    return prompt

async def generate_blog_with_gemini(images: List[Dict], style: str, store_url: Optional[str] = None) -> Dict:
    """Gemini APIを使用してブログを生成する
    
    Args:
        images: 画像情報のリスト
        style: 文体スタイル
        store_url: HPB店舗URL（任意）
        
    Returns:
        Dict: 生成されたブログデータ（title, body）
    """
    try:
        # APIの初期設定
        setup_gemini_api()
        
        # プロンプトの生成
        prompt = build_gemini_prompt(images, style, store_url)
        
        # モデルの選択
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # 画像データの準備
        image_parts = []
        for img_info in images:
            with open(img_info['path'], 'rb') as f:
                image_data = f.read()
                image_parts.append({
                    'data': image_data,
                    'mime_type': 'image/jpeg'  # 実際のMIMEタイプに応じて調整が必要
                })
        
        # APIリクエスト
        response = await model.generate_content_async([prompt] + image_parts)
        
        # レスポンスの解析
        response_text = response.text
        
        # レスポンスからJSON部分を抽出
        import json
        import re
        
        # JSON形式のデータを抽出するパターン
        json_pattern = r'```json\s*({[\s\S]*?})\s*```|```\s*({[\s\S]*?})\s*```|({[\s\S]*?})'
        match = re.search(json_pattern, response_text)
        
        if match:
            # マッチしたグループのうち、Noneでない最初のものを使用
            json_str = next((g for g in match.groups() if g is not None), None)
            
            try:
                result = json.loads(json_str)
                return {
                    'title': result.get('title', 'タイトルが生成できませんでした'),
                    'body': result.get('body', '本文が生成できませんでした')
                }
            except (json.JSONDecodeError, TypeError):
                # JSON解析に失敗した場合は、テキスト処理に移行
                pass
        
        # JSON解析に失敗した場合、テキストを整形して処理
        # マークダウンやコードブロックのマーカーを除去
        cleaned_text = re.sub(r'```(json)?|```', '', response_text)
        # 先頭の不要な文字を除去
        cleaned_text = re.sub(r'^[\s\n]*[\'"]*json[\'"]*', '', cleaned_text)
        
        # テキストを行に分割
        lines = cleaned_text.strip().split('\n')
        
        # 空行を除去
        lines = [line for line in lines if line.strip()]
        
        if len(lines) > 1:
            # 最初の行をタイトル、残りを本文として扱う
            return {
                'title': lines[0].strip(),
                'body': '\n'.join(lines[1:]).strip()
            }
        else:
            return {
                'title': '自動生成ブログ',
                'body': cleaned_text.strip()
            }
    
    except Exception as e:
        current_app.logger.error(f"Gemini API呼び出しエラー: {str(e)}")
        return {
            'title': 'エラーが発生しました',
            'body': f'ブログの生成中にエラーが発生しました。もう一度お試しください。詳細: {str(e)}'
        }
