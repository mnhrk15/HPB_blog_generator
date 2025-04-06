import os
import asyncio
from flask import (
    render_template, request, session, redirect,
    url_for, flash, current_app, jsonify
)
from werkzeug.utils import secure_filename
from . import bp
from ...utils.decorators import login_required
from ...utils.helpers import save_uploaded_image, clean_session_images, is_valid_image
from .services import generate_blog_with_gemini
from .scraping import scrape_hpb_data
from .sb_automation import post_to_sb

@bp.route('/')
@login_required
def index():
    """ブログ機能のインデックスページ（作成画面にリダイレクト）"""
    return redirect(url_for('blog.create'))

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    """ブログ作成入力画面"""
    if request.method == 'POST':
        # フォームデータの取得
        store_url = request.form.get('store_url')
        template_text = request.form.get('template_text')
        style = request.form.get('style', 'casual')  # デフォルトはカジュアル文体
        
        # 画像ファイルの取得
        files = request.files.getlist('images')
        
        # バリデーション
        error = None
        
        if not store_url:
            error = 'HPB店舗URLを入力してください。'
        elif not files or files[0].filename == '':
            error = '少なくとも1枚の画像をアップロードしてください。'
        
        if error is None:
            # 前回のセッション画像を削除
            clean_session_images(session.get('uploaded_images', []))
            
            # 画像を保存して情報をセッションに格納
            uploaded_images = []
            
            for i, file in enumerate(files):
                if file and file.filename != '' and is_valid_image(file):
                    img_info = save_uploaded_image(file)
                    # プレースホルダーを設定（[IMAGE_1], [IMAGE_2], ...）
                    img_info['placeholder'] = f"[IMAGE_{i+1}]"
                    uploaded_images.append(img_info)
            
            if not uploaded_images:
                flash('有効な画像がありません。JPEG, PNG, GIF, WEBPのみ対応しています。')
                return render_template('blog/create.html')
            
            # セッションに情報を保存
            session['store_url'] = store_url
            session['template_text'] = template_text
            session['style'] = style
            session['uploaded_images'] = uploaded_images
            
            # ブログ生成処理へ進む
            return redirect(url_for('blog.generate'))
        
        flash(error)
    
    return render_template('blog/create.html')

@bp.route('/generate')
@login_required
def generate():
    """ブログ生成処理（Gemini API連携とスクレイピング）"""
    # セッションから必要な情報を取得
    store_url = session.get('store_url')
    uploaded_images = session.get('uploaded_images')
    template_text = session.get('template_text', '')
    style = session.get('style', 'casual')
    
    if not store_url or not uploaded_images:
        flash('必要な情報が不足しています。最初からやり直してください。')
        return redirect(url_for('blog.create'))
    
    try:
        # HPBスクレイピング処理を実行
        scraped_data = scrape_hpb_data(store_url)
        session['scraped_data'] = scraped_data
        
        # Gemini APIによるブログ生成処理を実行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        generated_data = loop.run_until_complete(
            generate_blog_with_gemini(uploaded_images, style, store_url)
        )
        loop.close()
        
        # テンプレートテキストがある場合は本文に追加
        if template_text:
            generated_data['body'] = generated_data['body'] + '\n\n' + template_text
        
        session['generated_data'] = generated_data
        
        # 編集画面へリダイレクト
        return redirect(url_for('blog.edit'))
    
    except Exception as e:
        current_app.logger.error(f"ブログ生成エラー: {str(e)}")
        flash(f'ブログの生成中にエラーが発生しました: {str(e)}')
        return redirect(url_for('blog.create'))

@bp.route('/edit')
@login_required
def edit():
    """編集・確認画面"""
    # セッションから必要な情報を取得
    store_url = session.get('store_url')
    uploaded_images = session.get('uploaded_images')
    generated_data = session.get('generated_data')
    scraped_data = session.get('scraped_data')
    
    if not store_url or not uploaded_images:
        flash('必要な情報が不足しています。最初からやり直してください。')
        return redirect(url_for('blog.create'))
    
    # 仮のデータ（実際にはGemini APIとスクレイピングの結果を使用）
    # この部分は後で実装します
    if not generated_data:
        generated_data = {
            'title': 'サンプルブログタイトル',
            'body': 'これはサンプルの本文です。[IMAGE_1]がここに挿入されます。'
        }
        session['generated_data'] = generated_data
    
    if not scraped_data:
        scraped_data = {
            'stylists': ['スタイリスト1', 'スタイリスト2'],
            'coupons': ['クーポンA', 'クーポンB']
        }
        session['scraped_data'] = scraped_data
    
    return render_template('blog/edit.html',
                          store_url=store_url,
                          images=uploaded_images,
                          generated_data=generated_data,
                          scraped_data=scraped_data)

@bp.route('/post_to_sb', methods=['POST'])
@login_required
def post_to_sb_route():
    """サロンボードへの投稿処理"""
    # フォームデータの取得
    sb_id = request.form.get('sb_id')
    sb_password = request.form.get('sb_password')
    title = request.form.get('title')
    body = request.form.get('body')
    stylist = request.form.get('stylist')
    coupon = request.form.get('coupon')
    
    # セッションから画像情報を取得
    uploaded_images = session.get('uploaded_images', [])
    
    # バリデーション
    error = None
    
    if not sb_id or not sb_password:
        error = 'サロンボードのIDとパスワードを入力してください。'
    elif not title or not body:
        error = 'タイトルと本文は必須です。'
    elif not stylist:
        error = 'スタイリストを選択してください。'
    elif not uploaded_images:
        error = '画像情報が見つかりません。最初からやり直してください。'
    
    if error is None:
        try:
            # サロンボード自動投稿処理を実行
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                post_to_sb(sb_id, sb_password, title, body, stylist, uploaded_images, coupon)
            )
            loop.close()
            
            if result['success']:
                flash(result['message'])
                # 投稿成功後、セッションをクリア
                clean_session_images(uploaded_images)
                session.pop('store_url', None)
                session.pop('template_text', None)
                session.pop('style', None)
                session.pop('uploaded_images', None)
                session.pop('generated_data', None)
                session.pop('scraped_data', None)
                return redirect(url_for('blog.create'))
            else:
                flash(f'投稿に失敗しました: {result["message"]}')
        
        except Exception as e:
            current_app.logger.error(f"サロンボード投稿エラー: {str(e)}")
            flash(f'投稿処理中にエラーが発生しました: {str(e)}')
    
    else:
        flash(error)
    
    return redirect(url_for('blog.edit'))
