from flask import (
    render_template, request, session, redirect,
    url_for, flash, current_app
)
from . import bp

@bp.route('/login', methods=('GET', 'POST'))
def login():
    """ログイン処理"""
    if request.method == 'POST':
        password = request.form.get('password')
        error = None
        
        # パスワードの検証
        if not password:
            error = 'パスワードが必要です。'
        elif password != current_app.config['APP_PASSWORD']:
            error = 'パスワードが正しくありません。'
        
        if error is None:
            # セッションのクリアとログイン状態の設定
            session.clear()
            session['logged_in'] = True
            return redirect(url_for('blog.create'))
        
        flash(error)
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    """ログアウト処理"""
    session.clear()
    return redirect(url_for('auth.login'))
