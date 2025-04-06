import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List, Optional
from flask import current_app
import re

def scrape_hpb_data(store_url: str) -> Dict:
    """HPBサイトからスタイリストとクーポン情報をスクレイピングする
    
    Args:
        store_url: HPB店舗URL
        
    Returns:
        Dict: スクレイピング結果（stylists, coupons）
    """
    # URLの正規化（末尾のスラッシュを確保）
    if not store_url.endswith('/'):
        store_url = store_url + '/'
    
    # セレクタ設定の取得
    selectors = current_app.config.get('SELECTORS', {})
    
    # スタイリスト情報の取得
    stylists = _scrape_stylists(store_url, selectors)
    
    # クーポン情報の取得
    coupons = _scrape_coupons(store_url, selectors)
    
    return {
        'stylists': stylists,
        'coupons': coupons
    }

def _scrape_stylists(store_url: str, selectors: Dict) -> List[str]:
    """スタイリスト情報をスクレイピングする
    
    Args:
        store_url: HPB店舗URL
        selectors: セレクタ設定
        
    Returns:
        List[str]: スタイリスト名のリスト
    """
    try:
        # URLが空またはNoneの場合は空リストを返す
        if not store_url:
            current_app.logger.error("店舗URLが空です")
            return []
            
        # URLの正規化（末尾のスラッシュを確保）
        if not store_url.endswith('/'):
            store_url = store_url + '/'
            
        # スタイリストページのURL生成
        stylist_url_suffix = selectors.get('hpb', {}).get('stylist', {}).get('page_url_suffix', 'stylist/')
        stylist_url = store_url + stylist_url_suffix
        
        current_app.logger.info(f"スタイリストページURL: {stylist_url}")
        
        # ページの取得
        response = requests.get(stylist_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        # HTMLの解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # スタイリストセクションを特定（アシスタントセクションと区別するため）
        stylist_section = soup.find('h2', string=lambda text: text and 'スタイリスト' in text and 'アシスタント' not in text)
        if not stylist_section:
            current_app.logger.error("スタイリストセクションが見つかりませんでした")
            return []
            
        # スタイリストセクションの次の要素を取得
        stylist_container = stylist_section.find_next('div', class_='oh')
        if not stylist_container:
            current_app.logger.error("スタイリストコンテナが見つかりませんでした")
            return []
            
        # スタイリスト名を取得（p.mT10.fs16.b > a セレクタを使用）
        stylist_elements = stylist_container.select('p.mT10.fs16.b > a')
        
        # スタイリスト名のリストを作成（整形せずそのまま取得）
        stylists = [element.text for element in stylist_elements if element.text]
        
        current_app.logger.info(f"スクレイピングされたスタイリスト数: {len(stylists)}")
        
        return stylists
    
    except Exception as e:
        current_app.logger.error(f"スタイリスト情報のスクレイピングエラー: {str(e)}")
        return []

def _scrape_coupons(store_url: str, selectors: Dict) -> List[str]:
    """クーポン情報をスクレイピングする
    
    Args:
        store_url: HPB店舗URL
        selectors: セレクタ設定
        
    Returns:
        List[str]: クーポン名のリスト
    """
    try:
        # URLが空またはNoneの場合は空リストを返す
        if not store_url:
            current_app.logger.error("店舗URLが空です")
            return []
            
        # URLの正規化（末尾のスラッシュを確保）
        if not store_url.endswith('/'):
            store_url = store_url + '/'
            
        # クーポンページのURL生成
        coupon_url_suffix = selectors.get('hpb', {}).get('coupon', {}).get('page_url_suffix', 'coupon/')
        coupon_url = store_url + coupon_url_suffix
        
        current_app.logger.info(f"クーポンページURL: {coupon_url}")
        
        # ページの取得
        response = requests.get(coupon_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response.raise_for_status()
        
        # HTMLの解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # クーポン名のセレクタを取得
        coupon_selector = selectors.get('hpb', {}).get('coupon', {}).get('coupon_name_selector')
        current_app.logger.info(f"使用するクーポンセレクタ: {coupon_selector}")
        
        # ページネーション情報の取得
        max_page = 1
        pagination_selector = selectors.get('hpb', {}).get('coupon', {}).get('pagination_selector', '.pa.bottom0.right0')
        pagination_element = soup.select_one(pagination_selector)
        
        if pagination_element:
            # ページネーション要素から最大ページ数を抽出
            pagination_text = pagination_element.text.strip()
            current_app.logger.info(f"ページネーションテキスト: {pagination_text}")
            
            # 「1/3ページ」のような形式から最大ページ数を抽出
            page_match = re.search(r'(\d+)/(\d+)', pagination_text)
            if page_match:
                max_page = int(page_match.group(2))
                current_app.logger.info(f"最大ページ数: {max_page}")
        
        # クーポン名のリスト
        coupons = []
        
        # 各ページのクーポン情報を取得
        for page in range(1, max_page + 1):
            current_page_url = coupon_url
            
            if page > 1:
                # 2ページ目以降のURL生成
                pagination_url_format = selectors.get('hpb', {}).get('coupon', {}).get('pagination_url_format', 'coupon/PN{n}.html')
                current_page_url = store_url + pagination_url_format.replace('{n}', str(page))
                current_app.logger.info(f"ページ{page}のURL: {current_page_url}")
                
                # ページの取得
                response = requests.get(current_page_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                response.raise_for_status()
                
                # HTMLの解析
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # クーポン要素を取得
            coupon_elements = []
            
            if coupon_selector:
                # カンマ区切りの複数セレクタをサポート
                selectors_list = [s.strip() for s in coupon_selector.split(',')]
                for selector in selectors_list:
                    elements = soup.select(selector)
                    if elements:
                        current_app.logger.info(f"セレクタ '{selector}' で{len(elements)}個のクーポン要素が見つかりました")
                        coupon_elements.extend(elements)
            
            # クーポン名をリストに追加
            for element in coupon_elements:
                # クーポンと通常メニューを区別
                is_coupon = True
                
                # クラス属性をチェック
                element_classes = element.get('class', [])
                if 'fl' in element_classes:  # 通常メニューは 'fl' クラスを持つ
                    is_coupon = False
                    current_app.logger.debug(f"通常メニューを除外: {element.text.strip()}")
                
                # 親要素のクラスもチェック
                parent = element.parent
                if parent and 'cFix' in parent.get('class', []):  # 通常メニューの親は 'cFix' クラスを持つことが多い
                    is_coupon = False
                    current_app.logger.debug(f"通常メニューの親要素を検出: {element.text.strip()}")
                
                # クーポンテキストを取得
                coupon_text = element.text.strip()
                # 注: 価格表記なしの場合も除外しないように変更
                
                # クーポンのみをリストに追加
                if is_coupon and coupon_text and coupon_text not in coupons and len(coupon_text) > 5:  # 短すぎるテキストは除外
                    coupons.append(coupon_text)
            
            # 過負荷を避けるための待機
            if page < max_page:
                time.sleep(1)
        
        current_app.logger.info(f"スクレイピングされたクーポン数: {len(coupons)}")
        return coupons
    
    except Exception as e:
        current_app.logger.error(f"クーポン情報のスクレイピングエラー: {str(e)}")
        return []
