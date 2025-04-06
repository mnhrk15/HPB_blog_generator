// 共通のJavaScript機能

// フラッシュメッセージの自動非表示
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.style.display = 'none';
            }, 500);
        }, 5000);
    });
});

// 画像プレビュー機能
function previewImages(input, previewContainer) {
    if (!input || !previewContainer) return;
    
    const files = input.files;
    
    // プレビューコンテナをクリア
    previewContainer.innerHTML = '';
    
    // 各ファイルに対してプレビュー要素を作成
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 画像ファイルのみ処理
        if (!file.type.startsWith('image/')) continue;
        
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const previewItem = document.createElement('div');
            previewItem.className = 'image-preview-item';
            
            const img = document.createElement('img');
            img.src = e.target.result;
            img.alt = file.name;
            
            const removeBtn = document.createElement('div');
            removeBtn.className = 'remove-btn';
            removeBtn.innerHTML = '×';
            removeBtn.dataset.index = i;
            removeBtn.addEventListener('click', function() {
                // この画像をプレビューから削除
                previewItem.remove();
                // TODO: 実際のファイル選択からも削除する機能を追加
            });
            
            previewItem.appendChild(img);
            previewItem.appendChild(removeBtn);
            previewContainer.appendChild(previewItem);
        };
        
        reader.readAsDataURL(file);
    }
}

// ローディングインジケータの表示/非表示
function showLoading() {
    const loading = document.querySelector('.loading');
    if (loading) loading.style.display = 'block';
}

function hideLoading() {
    const loading = document.querySelector('.loading');
    if (loading) loading.style.display = 'none';
}
