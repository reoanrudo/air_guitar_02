/**
 * QRコードペアリング機能
 *
 * スマートフォンとPCのペアリングを管理する
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM要素
    const showQrBtn = document.getElementById('show-qr-btn');
    const qrModal = document.getElementById('qr-modal');
    const qrClose = document.querySelector('.qr-close');
    const qrCode = document.getElementById('qr-code');
    const pairingStatus = document.getElementById('pairing-status');
    const refreshQrBtn = document.getElementById('refresh-qr-btn');

    // セッションID（テンプレートから埋め込まれる）
    const sessionId = qrCode.dataset.sessionId || '';

    /**
     * QRモーダルを表示する
     */
    function showQrModal() {
        qrModal.style.display = 'block';
        refreshQrCode();
    }

    /**
     * QRモーダルを閉じる
     */
    function closeQrModal() {
        qrModal.style.display = 'none';
    }

    /**
     * QRコードを更新する
     */
    function refreshQrCode() {
        // タイムスタンプを追加してキャッシュを回避
        const timestamp = new Date().getTime();
        qrCode.src = `/guitar/qr/?session=${sessionId}&t=${timestamp}`;
        pairingStatus.textContent = 'QRコードを読み込んでいます...';

        // QRコード読み込み完了
        qrCode.onload = function() {
            pairingStatus.textContent = 'スマートフォンでこのQRコードをスキャンしてください';
        };

        // QRコード読み込みエラー
        qrCode.onerror = function() {
            pairingStatus.textContent = 'QRコードの読み込みに失敗しました';
        };
    }

    // QRコードにセッションIDを設定
    if (sessionId) {
        qrCode.dataset.sessionId = sessionId;
    }

    // イベントリスナー
    if (showQrBtn) {
        showQrBtn.addEventListener('click', showQrModal);
    }
    if (qrClose) {
        qrClose.addEventListener('click', closeQrModal);
    }
    if (refreshQrBtn) {
        refreshQrBtn.addEventListener('click', refreshQrCode);
    }

    // モーダル外クリックで閉じる
    window.addEventListener('click', function(event) {
        if (event.target === qrModal) {
            closeQrModal();
        }
    });
});
