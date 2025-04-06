import os
import sys
import time
from playwright.sync_api import sync_playwright

def test_playwright():
    """Playwrightの基本的な機能をテストする"""
    print("Playwrightテスト開始")
    
    browser = None
    try:
        # 同期APIを使用する
        playwright = sync_playwright().start()
        
        # ブラウザを起動（ヘッドレスモードなし）
        # macOSでの安定性向上のためのオプションを追加
        browser = playwright.chromium.launch(
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
        
        # コンテキストを作成（タイムアウト設定を含む）
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        
        # 新しいページを開く
        page = context.new_page()
        
        # Googleにアクセス
        print("Googleにアクセスします...")
        page.goto('https://www.google.com/', timeout=15000)
        
        # タイトルを取得して表示
        title = page.title()
        print(f"ページタイトル: {title}")
        
        # スクリーンショットを撮る
        print("スクリーンショットを撮影します...")
        page.screenshot(path='screenshot.png')
        
        # 検索ボックスが表示されるまで待機
        print("検索ボックスが表示されるまで待機します...")
        # 複数の可能性のあるセレクタを試す
        try:
            page.wait_for_selector('input[name="q"]', timeout=5000)
            search_selector = 'input[name="q"]'
        except Exception:
            try:
                page.wait_for_selector('textarea[name="q"]', timeout=5000)
                search_selector = 'textarea[name="q"]'
            except Exception:
                try:
                    page.wait_for_selector('input[title="検索"]', timeout=5000)
                    search_selector = 'input[title="検索"]'
                except Exception:
                    search_selector = '.gLFyf'  # Googleの検索ボックスのクラス名
        
        # 検索ボックスに入力
        print(f"検索ボックスに「Playwright」と入力します... (セレクタ: {search_selector})")
        page.fill(search_selector, 'Playwright')
        
        # 検索ボタンをクリック（ボタンが見つからない場合はEnterキーを押す）
        print("検索ボタンをクリックします...")
        try:
            # 検索ボタンが表示されるまで待機
            page.wait_for_selector('input[name="btnK"]:visible', timeout=5000)
            page.click('input[name="btnK"]')
        except Exception as e:
            print(f"検索ボタンが見つからないためEnterキーを押します: {e}")
            # 先ほど特定した検索ボックスにEnterキーを押す
            page.press(search_selector, 'Enter')
        
        # 結果が表示されるまで待機
        print("検索結果が表示されるまで待機します...")
        try:
            page.wait_for_selector('#search', timeout=10000)
        except Exception as e:
            print(f"#search セレクタが見つかりませんでした: {e}")
            try:
                # 代替のセレクタを試す
                page.wait_for_selector('#rso', timeout=5000)
                print("#rso セレクタが見つかりました")
            except Exception as e2:
                print(f"検索結果のセレクタが見つかりませんでした: {e2}")
                # 検索結果が表示されるまで少し待機
                time.sleep(3)
        
        # 最終的なタイトルを取得
        final_title = page.title()
        print(f"検索結果ページタイトル: {final_title}")
        
        # 5秒待機してからブラウザを閉じる
        print("5秒待機します...")
        time.sleep(5)
        
        # コンテキストを閉じる
        context.close()
        
        # ブラウザを閉じる
        print("ブラウザを閉じます...")
        browser.close()
        
        # Playwrightを停止
        playwright.stop()
        
        print("Playwrightテスト完了")
        return True
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False
    finally:
        # 確実にブラウザを閉じる
        if browser:
            try:
                browser.close()
            except:
                print("ブラウザの終了処理中にエラーが発生しました")

if __name__ == "__main__":
    success = test_playwright()
    # 終了コードを設定
    sys.exit(0 if success else 1)
