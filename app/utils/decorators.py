from functools import wraps
from flask import session, redirect, url_for

def login_required(view):
    """ログインが必要なビュー関数のデコレータ"""
    @wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view
