/**
 * モバイルコントローラー - HTTPポーリング方式
 *
 * スマートフォンからギターを操作するための機能
 * HTTPポーリングでPCと通信（WebSocketの代替案）
 */

// グローバルスコープでクラスを定義
(function() {
    'use strict';

    // コードの指板図データ（弦番号: フレット番号: 指番）
    const CHORD_DIAGRAMS = {
        'C': [
            { string: 6, fret: 0, finger: null },
            { string: 5, fret: 3, finger: 3 },
            { string: 4, fret: 2, finger: 2 },
            { string: 3, fret: 0, finger: null },
            { string: 2, fret: 1, finger: 1 },
            { string: 1, fret: 0, finger: null },
        ],
        'D': [
            { string: 6, fret: 0, finger: null },
            { string: 5, fret: 0, finger: null },
            { string: 4, fret: 0, finger: null },
            { string: 3, fret: 2, finger: 2 },
            { string: 2, fret: 3, finger: 3 },
            { string: 1, fret: 2, finger: 4 },
        ],
        'E': [
            { string: 6, fret: 0, finger: null },
            { string: 5, fret: 0, finger: null },
            { string: 4, fret: 0, finger: null },
            { string: 3, fret: 1, finger: 1 },
            { string: 2, fret: 2, finger: 3 },
            { string: 1, fret: 0, finger: null },
        ],
        'F': [
            { string: 6, fret: 0, finger: null },
            { string: 5, fret: 0, finger: null },
            { string: 4, fret: 0, finger: null },
            { string: 3, fret: 2, finger: 2 },
            { string: 2, fret: 1, finger: 1 },
            { string: 1, fret: 1, finger: 1 },
        ],
        'G': [
            { string: 6, fret: 3, finger: 2 },
            { string: 5, fret: 2, finger: 1 },
            { string: 4, fret: 0, finger: null },
            { string: 3, fret: 0, finger: null },
            { string: 2, fret: 0, finger: null },
            { string: 1, fret: 3, finger: 3 },
        ],
        'A': [
            { string: 6, fret: 0, finger: null },
            { string: 5, fret: 0, finger: null },
            { string: 4, fret: 2, finger: 2 },
            { string: 3, fret: 2, finger: 2 },
            { string: 2, fret: 2, finger: 2 },
            { string: 1, fret: 0, finger: null },
        ],
        'Am': [
            { string: 6, fret: 0, finger: null },
            { string: 5, fret: 0, finger: null },
            { string: 4, fret: 2, finger: 2 },
            { string: 3, fret: 2, finger: 3 },
            { string: 2, fret: 1, finger: 1 },
            { string: 1, fret: 0, finger: null },
        ],
        'Em': [
            { string: 6, fret: 0, finger: null },
            { string: 5, fret: 2, finger: 2 },
            { string: 4, fret: 2, finger: 2 },
            { string: 3, fret: 0, finger: null },
            { string: 2, fret: 0, finger: null },
            { string: 1, fret: 0, finger: null },
        ],
    };

    class MobileControllerPolling {
        constructor() {
            // DOM要素
            this.statusDot = document.getElementById('status-dot');
            this.statusText = document.getElementById('status-text');
            this.activityDot = document.getElementById('activity-dot');
            this.activityText = document.getElementById('activity-text');
            this.connectionMessage = document.getElementById('connection-message');
            this.sessionIdInput = document.getElementById('session-id');
            this.connectBtn = document.getElementById('connect-btn');
            this.pairingSection = document.getElementById('pairing-section');
            this.chordSection = document.getElementById('chord-section');
            this.practiceSection = document.getElementById('practice-section');
            this.startPracticeBtn = document.getElementById('start-practice-btn');
            this.stopPracticeBtn = document.getElementById('stop-practice-btn');
            this.timerDisplay = document.getElementById('timer-display');
            this.practiceStatusText = document.getElementById('practice-status-text');
            this.currentChordDisplay = document.getElementById('current-chord-display');
            this.diagramChordName = document.getElementById('diagram-chord-name');
            this.diagramStrings = document.getElementById('diagram-strings');
            this.cameraCanvas = document.getElementById('camera-feed');
            this.cameraPlaceholder = document.querySelector('.camera-placeholder');

            // 接続状態
            this.isConnected = false;
            this.sessionId = null;

            // ポーリング
            this.pollingInterval = null;
            this.pollingRate = 1000; // 1秒ごとにポーリング

            // 練習セッション
            this.isPracticing = false;
            this.practiceStartTime = null;
            this.timerInterval = null;
            this.currentChord = null;

            // カメラ
            this.cameraContext = null;

            // 初期化
            this.initialize();
        }

        /**
         * 初期化処理
         */
        initialize() {
            this.bindEvents();
            this.loadSessionIdFromUrl();
            this.initializeFretboardDiagram();
            this.initializeCameraCanvas();

            // ページ可視性の監視
            document.addEventListener('visibilitychange', () => {
                if (document.hidden && this.isPracticing) {
                    this.showWarning('練習中に画面を離れました');
                }
            });
        }

        /**
         * 指板図を初期化
         */
        initializeFretboardDiagram() {
            this.renderFretboardDiagram('-');
        }

        /**
         * 指板図をレンダリング
         * @param {string} chordName - コード名
         */
        renderFretboardDiagram(chordName) {
            if (!this.diagramStrings) return;

            const positions = CHORD_DIAGRAMS[chordName] || [];
            this.diagramStrings.innerHTML = '';

            for (let stringNum = 6; stringNum >= 1; stringNum--) {
                const stringRow = document.createElement('div');
                stringRow.className = 'diagram-string';

                const stringLabel = document.createElement('span');
                stringLabel.className = 'string-label';
                stringLabel.textContent = `${stringNum}`;
                stringRow.appendChild(stringLabel);

                const fretsDiv = document.createElement('div');
                fretsDiv.className = 'diagram-frets';

                for (let fretNum = 0; fretNum <= 5; fretNum++) {
                    const fret = document.createElement('div');
                    fret.className = 'diagram-fret';

                    const position = positions.find(p => p.string === stringNum && p.fret === fretNum);
                    if (position && position.finger) {
                        const fingerDot = document.createElement('div');
                        fingerDot.className = 'finger-dot';
                        fingerDot.textContent = position.finger;
                        fret.appendChild(fingerDot);
                    }
                    fretsDiv.appendChild(fret);
                }

                stringRow.appendChild(fretsDiv);
                this.diagramStrings.appendChild(stringRow);
            }

            if (this.diagramChordName) {
                this.diagramChordName.textContent = chordName;
            }
        }

        /**
         * カメラキャンバスを初期化
         */
        initializeCameraCanvas() {
            if (this.cameraCanvas) {
                this.cameraContext = this.cameraCanvas.getContext('2d');
            }
        }

        /**
         * イベントリスナーのバインド
         */
        bindEvents() {
            // 接続ボタン
            if (this.connectBtn) {
                this.connectBtn.addEventListener('click', () => this.connect());
            }

            // 練習コントロール
            if (this.startPracticeBtn) {
                this.startPracticeBtn.addEventListener('click', () => this.startPractice());
            }
            if (this.stopPracticeBtn) {
                this.stopPracticeBtn.addEventListener('click', () => this.stopPractice());
            }

            // コードボタン
            const chordBtns = document.querySelectorAll('.chord-btn');
            chordBtns.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const chord = e.currentTarget.dataset.chord;
                    this.selectChord(chord);
                });
            });

            // ページ離脱時のクリーンアップ
            window.addEventListener('beforeunload', () => {
                this.cleanup();
            });
        }

        /**
         * URLパラメータからセッションIDを取得して設定
         */
        loadSessionIdFromUrl() {
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = urlParams.get('session');

            if (sessionId) {
                this.sessionIdInput.value = sessionId;
                this.showMessage('セッションIDが設定されました。接続中...', 'info');
                // 自動的に接続を試みる
                setTimeout(() => this.connect(), 500);
            }
        }

        /**
         * 接続を開始
         */
        async connect() {
            this.sessionId = this.sessionIdInput.value.trim();

            if (!this.sessionId) {
                this.showMessage('セッションIDを入力してください', 'error');
                return;
            }

            this.connectBtn.disabled = true;
            this.connectBtn.textContent = '接続中...';
            this.showMessage('接続を試みています...', 'info');
            this.updateActivity(false);

            try {
                // 接続確認
                const response = await fetch('/mobile/api/poll/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ session_id: this.sessionId })
                });

                if (response.ok) {
                    this.isConnected = true;
                    this.updateConnectionStatus(true);
                    this.updateActivity(true);
                    this.showMessage('接続に成功しました！', 'success');
                    this.enableController();
                    this.startPolling();
                } else {
                    throw new Error('接続に失敗しました');
                }
            } catch (error) {
                console.error('接続エラー:', error);
                this.showMessage('接続に失敗しました。もう一度お試しください。', 'error');
                this.updateActivity(false);
                this.resetConnectButton();
            }
        }

        /**
         * ポーリングを開始
         */
        startPolling() {
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
            }

            // 即座に1回実行
            this.poll();

            // 定期的にポーリング
            this.pollingInterval = setInterval(() => {
                this.poll();
            }, this.pollingRate);
        }

        /**
         * ポーリング - PCの状態を取得
         */
        async poll() {
            if (!this.isConnected || !this.sessionId) return;

            try {
                const response = await fetch('/mobile/api/poll/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ session_id: this.sessionId })
                });

                if (response.ok) {
                    const data = await response.json();

                    // カメラフレームを更新
                    if (data.camera_frame) {
                        this.displayCameraFrame(data.camera_frame);
                    }

                    this.updateActivity(true);
                } else {
                    console.error('ポーリングエラー:', response.status);
                    this.updateActivity(false);
                }
            } catch (error) {
                console.error('ポーリングエラー:', error);
                this.updateActivity(false);
            }
        }

        /**
         * カメラフレームを表示
         * @param {string} base64Data - Base64エンコードされた画像データ
         */
        displayCameraFrame(base64Data) {
            if (!this.cameraContext) return;

            const img = new Image();
            img.onload = () => {
                this.cameraCanvas.width = img.width || this.cameraCanvas.width;
                this.cameraCanvas.height = img.height || this.cameraCanvas.height;
                this.cameraContext.drawImage(img, 0, 0);

                if (this.cameraPlaceholder) {
                    this.cameraPlaceholder.style.display = 'none';
                }
            };
            img.src = `data:image/jpeg;base64,${base64Data}`;
        }

        /**
         * コマンドを送信
         * @param {string} command - コマンド名
         * @param {object} params - パラメータ
         */
        async sendCommand(command, params = {}) {
            if (!this.isConnected || !this.sessionId) return;

            try {
                const response = await fetch('/mobile/api/command/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Timestamp': Date.now().toString(),
                    },
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        command: command,
                        params: params
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        console.log('コマンド送信成功:', command);
                    }
                } else {
                    console.error('コマンド送信エラー:', response.status);
                }
            } catch (error) {
                console.error('コマンド送信エラー:', error);
            }
        }

        /**
         * コードを選択
         * @param {string} chordName - コード名
         */
        selectChord(chordName) {
            this.currentChord = chordName;

            // UIを更新
            if (this.currentChordDisplay) {
                this.currentChordDisplay.textContent = chordName;
            }

            // 指板図を更新
            this.renderFretboardDiagram(chordName);

            // コマンドを送信
            this.sendCommand('chord_change', { chord: chordName });

            // タップフィードバック
            const btn = document.querySelector(`.chord-btn[data-chord="${chordName}"]`);
            if (btn) {
                btn.classList.add('tapped');
                setTimeout(() => btn.classList.remove('tapped'), 300);
            }

            this.showMessage(`コード「${chordName}」を選択しました`, 'success');
        }

        /**
         * 練習を開始
         */
        async startPractice() {
            this.isPracticing = true;
            this.practiceStartTime = Date.now();
            this.startTimer();
            this.updatePracticeButtons();
            this.practiceStatusText.textContent = '練習中...';

            await this.sendCommand('practice_start');
            this.showMessage('練習を開始しました！', 'success');
        }

        /**
         * 練習を終了
         */
        async stopPractice() {
            this.isPracticing = false;
            this.stopTimer();
            this.updatePracticeButtons();
            this.practiceStatusText.textContent = '練習未開始';

            await this.sendCommand('practice_end');
            this.showMessage('練習を終了しました', 'info');
        }

        /**
         * タイマーを開始
         */
        startTimer() {
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
            }

            this.timerInterval = setInterval(() => {
                const elapsed = Date.now() - this.practiceStartTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                this.timerDisplay.textContent =
                    `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }, 1000);
        }

        /**
         * タイマーを停止
         */
        stopTimer() {
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        }

        /**
         * 練習ボタンの状態を更新
         */
        updatePracticeButtons() {
            if (this.startPracticeBtn && this.stopPracticeBtn) {
                this.startPracticeBtn.disabled = this.isPracticing;
                this.stopPracticeBtn.disabled = !this.isPracticing;
            }
        }

        /**
         * 接続状態を更新
         * @param {boolean} connected - 接続状態
         */
        updateConnectionStatus(connected) {
            if (this.statusDot && this.statusText) {
                if (connected) {
                    this.statusDot.classList.add('connected');
                    this.statusText.textContent = '接続中';
                } else {
                    this.statusDot.classList.remove('connected');
                    this.statusText.textContent = '未接続';
                }
            }
        }

        /**
         * アクティビティインジケーターを更新
         * @param {boolean} active - アクティブ状態
         */
        updateActivity(active) {
            if (this.activityDot && this.activityText) {
                if (active) {
                    this.activityDot.classList.add('active');
                    this.activityText.textContent = '通信中';
                } else {
                    this.activityDot.classList.remove('active');
                    this.activityText.textContent = '待機中';
                }
            }
        }

        /**
         * コントローラーを有効化
         */
        enableController() {
            this.pairingSection?.classList.add('hidden');
            this.chordSection?.classList.remove('disabled');
            this.practiceSection?.classList.remove('disabled');
        }

        /**
         * コントローラーを無効化
         */
        disableController() {
            this.pairingSection?.classList.remove('hidden');
            this.chordSection?.classList.add('disabled');
            this.practiceSection?.classList.add('disabled');
        }

        /**
         * 接続ボタンをリセット
         */
        resetConnectButton() {
            if (this.connectBtn) {
                this.connectBtn.disabled = false;
                this.connectBtn.textContent = '接続';
            }
        }

        /**
         * メッセージを表示
         * @param {string} message - メッセージ
         * @param {string} type - メッセージタイプ
         */
        showMessage(message, type = 'info') {
            if (this.connectionMessage) {
                this.connectionMessage.textContent = message;
                this.connectionMessage.className = `message ${type}`;
            }
        }

        /**
         * 警告を表示
         * @param {string} message - 警告メッセージ
         */
        showWarning(message) {
            this.showMessage(message, 'warning');
        }

        /**
         * クリーンアップ
         */
        cleanup() {
            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        }
    }

    // ページ読み込み時に初期化
    document.addEventListener('DOMContentLoaded', function() {
        window.mobileController = new MobileControllerPolling();
    });

})();
