/**
 * QRコードペアリング機能
 *
 * スマートフォンとPCのペアリングを管理する
 * IPアドレス表示とセッション管理
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM要素
    const showQrBtn = document.getElementById('show-qr-btn');
    const qrModal = document.getElementById('qr-modal');
    const qrClose = document.querySelector('.qr-close');
    const qrCode = document.getElementById('qr-code');
    const pairingStatus = document.getElementById('pairing-status');
    const refreshQrBtn = document.getElementById('refresh-qr-btn');
    const localIpSpan = document.getElementById('local-ip');
    const sessionIdSpan = document.getElementById('session-id-display');

    // ペアリング状態
    let pairingInterval = null;
    let currentSessionId = null;
    let currentLocalIp = null;

    /**
     * PCのローカルIPアドレスを取得
     */
    async function getLocalIpAddress() {
        // Cloudflare TunnelのURLを返す
        return 'yang-deborah-especially-luke.trycloudflare.com';
    }

    /**
     * QRモーダルを表示する
     */
    function showQrModal() {
        qrModal.style.display = 'block';
        refreshQrCode();
        startPairingCheck();
    }

    /**
     * QRモーダルを閉じる
     */
    function closeQrModal() {
        qrModal.style.display = 'none';
        stopPairingCheck();
    }

    /**
     * QRコードを更新する
     */
    async function refreshQrCode() {
        // タイムスタンプを追加してキャッシュを回避
        const timestamp = new Date().getTime();
        qrCode.src = `/mobile/qr/?t=${timestamp}`;
        pairingStatus.textContent = '待機中...';
        pairingStatus.className = 'pairing-status waiting';

        // QRコードからセッションIDを取得
        try {
            // セッションIDを取得（API経由）
            const response = await fetch('/mobile/api/current-session/');
            if (response.ok) {
                const data = await response.json();
                if (data.session_id) {
                    currentSessionId = data.session_id;
                    sessionIdSpan.textContent = currentSessionId.substring(0, 8) + '...'; // 短縮表示
                    console.log('Current session ID:', currentSessionId);
                }
            }
        } catch (error) {
            console.error('Failed to get session ID:', error);
        }
    }

    /**
     * ペアリング状態のチェックを開始する
     */
    function startPairingCheck() {
        // 5秒ごとにペアリング状態をチェック
        pairingInterval = setInterval(checkPairingStatus, 5000);
    }

    /**
     * ペアリング状態のチェックを停止する
     */
    function stopPairingCheck() {
        if (pairingInterval) {
            clearInterval(pairingInterval);
            pairingInterval = null;
        }
    }

    /**
     * ペアリング状態をチェックする
     * Note: 現在はデモ用の簡易実装
     * 実際にはHTTPポーリングで状態を受信する
     */
    function checkPairingStatus() {
        // TODO: HTTPポーリング経由でペアリング状態を確認
        // 現在はデモ用にランダムに変化させる
        const states = ['waiting', 'paired', 'connected'];
        const currentState = pairingStatus.dataset.state || 'waiting';

        if (currentState === 'waiting') {
            // ランダムにペアリング成功をシミュレート
            if (Math.random() > 0.7) {
                updatePairingStatus('paired');
            }
        } else if (currentState === 'paired') {
            // ランダムに接続完了をシミュレート
            if (Math.random() > 0.5) {
                updatePairingStatus('connected');
            }
        }
    }

    /**
     * ペアリングステータスを更新する
     * @param {string} status - ステータス（waiting, paired, connected）
     */
    function updatePairingStatus(status) {
        pairingStatus.dataset.state = status;

        switch (status) {
            case 'waiting':
                pairingStatus.textContent = '待機中...';
                pairingStatus.className = 'pairing-status waiting';
                break;
            case 'paired':
                pairingStatus.textContent = 'ペアリング完了！接続中...';
                pairingStatus.className = 'pairing-status paired';
                break;
            case 'connected':
                pairingStatus.textContent = '接続完了！スマートフォンで操作できます';
                pairingStatus.className = 'pairing-status connected';
                stopPairingCheck();
                // 3秒後にモーダルを閉じる
                setTimeout(closeQrModal, 3000);
                break;
        }
    }

    /**
     * 初期化処理
     */
    async function initialize() {
        // IPアドレスを取得して表示
        currentLocalIp = await getLocalIpAddress();
        localIpSpan.textContent = currentLocalIp;

        // QRコードボタンのテキストを変更
        if (showQrBtn) {
            showQrBtn.textContent = 'QRコードを表示';
        }
    }

    // 初期化を実行
    initialize();

    // イベントリスナー
    showQrBtn.addEventListener('click', showQrModal);
    qrClose.addEventListener('click', closeQrModal);
    refreshQrBtn.addEventListener('click', refreshQrCode);

    // モーダル外クリックで閉じる
    window.addEventListener('click', function(event) {
        if (event.target === qrModal) {
            closeQrModal();
        }
    });

    // ページ離脱時のクリーンアップ
    window.addEventListener('beforeunload', function() {
        stopPairingCheck();
    });
});
