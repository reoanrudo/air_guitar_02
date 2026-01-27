/**
 * モバイルコントローラー
 *
 * スマートフォンからギターを操作するための機能
 * WebSocket通信でPCとリアルタイム連携
 * 指板図表示、カメラ映像受信機能付き
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

    class MobileController {
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

            // WebSocket接続
            this.ws = null;
            this.isConnected = false;
            this.reconnectAttempts = 0;
            this.maxReconnectAttempts = 3;

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
            this.setupAutoReconnect();
            this.initializeFretboardDiagram();
            this.initializeCameraCanvas();
            this.startHeartbeat();

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

            // 既存の要素をクリア
            this.diagramStrings.innerHTML = '';

            // 弦ごとの行を作成
            for (let stringNum = 6; stringNum >= 1; stringNum--) {
                const stringRow = document.createElement('div');
                stringRow.className = 'diagram-string';

                // 弦ラベル
                const label = document.createElement('span');
                label.className = 'string-label';
                label.textContent = `${stringNum}弦`;
                stringRow.appendChild(label);

                // フレット領域
                const fretsDiv = document.createElement('div');
                fretsDiv.className = 'diagram-frets';

                // 5フレット分作成
                for (let fretNum = 0; fretNum <= 5; fretNum++) {
                    const fret = document.createElement('div');
                    fret.className = 'diagram-fret';

                    // この弦とフレットの組み合わせに対応する指を見つける
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

            // コード名を更新
            if (this.diagramChordName) {
                this.diagramChordName.textContent = chordName;
            }
        }

        /**
         * カメラキャンバスを初期化
         */
        initializeCameraCanvas() {
            if (!this.cameraCanvas) return;

            // キャンバスのサイズを設定
            const container = this.cameraCanvas.parentElement;
            this.cameraCanvas.width = container.clientWidth;
            this.cameraCanvas.height = container.clientHeight;

            // コンテキストを取得
            this.cameraContext = this.cameraCanvas.getContext('2d');
        }

        /**
         * イベントリスナーのバインド
         */
        bindEvents() {
            // 接続ボタン
            if (this.connectBtn) {
                this.connectBtn.addEventListener('click', () => this.connectWebSocket());
            }

            // 練習コントロール
            if (this.startPracticeBtn) {
                this.startPracticeBtn.addEventListener('click', () => this.startPractice());
            }

            if (this.stopPracticeBtn) {
                this.stopPracticeBtn.addEventListener('click', () => this.stopPractice());
            }

            // コードボタン
            document.querySelectorAll('.chord-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const chordName = e.currentTarget.dataset.chord;
                    this.selectChord(chordName);

                    // タップフィードバック
                    e.currentTarget.classList.add('tapped');
                    setTimeout(() => {
                        e.currentTarget.classList.remove('tapped');
                    }, 300);
                });

                // タッチフィードバック
                btn.addEventListener('touchstart', (e) => {
                    e.currentTarget.classList.add('active');
                });
                btn.addEventListener('touchend', (e) => {
                    e.currentTarget.classList.remove('active');
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
                this.showMessage(
                    'セッションIDが設定されました。接続中...',
                    'info'
                );
                // 自動的に接続を試みる
                setTimeout(() => this.connectWebSocket(), 500);
            }
        }

        /**
         * ハートビートを開始（接続監視用）
         */
        startHeartbeat() {
            setInterval(() => {
                if (this.isConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
                }
            }, 30000); // 30秒ごとにping
        }

        /**
         * WebSocket接続を確立する
         */
        connectWebSocket() {
            const sessionId = this.sessionIdInput.value.trim();

            if (!sessionId) {
                this.showMessage('セッションIDを入力してください', 'error');
                return;
            }

            // 接続中のメッセージ
            this.connectBtn.disabled = true;
            this.connectBtn.textContent = '接続中...';
            this.showMessage('接続を試みています...', 'info');
            this.updateActivity(false);

            // WebSocket接続
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/guitar/${sessionId}/`;

            try {
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket接続確立');
                    this.onWebSocketConnect();
                };

                this.ws.onmessage = (event) => {
                    this.handleWebSocketMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocketエラー:', error);
                    this.onWebSocketError();
                };

                this.ws.onclose = () => {
                    console.log('WebSocket接続終了');
                    this.onWebSocketDisconnect();
                };

            } catch (error) {
                console.error('WebSocket接続エラー:', error);
                this.showMessage(`接続に失敗しました: ${error.message}`, 'error');
                this.resetConnectButton();
            }
        }

        /**
         * WebSocket接続成功時の処理
         */
        onWebSocketConnect() {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            this.updateActivity(true);
            this.showMessage('接続に成功しました！', 'success');
            this.enableController();
        }

        /**
         * WebSocketエラー時の処理
         */
        onWebSocketError() {
            this.showMessage('接続エラーが発生しました', 'error');
            this.resetConnectButton();
            this.updateActivity(false);
        }

        /**
         * WebSocket切断時の処理
         */
        onWebSocketDisconnect() {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.updateActivity(false);
            this.disableController();

            if (this.isPracticing) {
                this.stopPractice();
            }

            // 再接続を試みる
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                this.showMessage(
                    `接続が切断されました。再接続を試みます... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
                    'info'
                );
                setTimeout(() => {
                    this.connectWebSocket();
                }, 2000);
            } else {
                this.showMessage('接続が切断されました。再度接続してください。', 'error');
            }
        }

        /**
         * WebSocketメッセージを処理する
         * @param {string} data - 受信したJSONデータ
         */
        handleWebSocketMessage(data) {
            try {
                const message = JSON.parse(data);

                switch (message.type) {
                    case 'connection_update':
                        this.handleConnectionUpdate(message);
                        break;

                    case 'chord_change':
                        this.handleChordChange(message);
                        break;

                    case 'practice_update':
                        this.handlePracticeUpdate(message);
                        break;

                    case 'camera_frame':
                        this.handleCameraFrame(message);
                        break;

                    case 'game_mode':
                        this.handleGameMode(message);
                        break;

                    case 'game_update':
                        this.handleGameUpdate(message);
                        break;

                    case 'judgement':
                        this.handleJudgement(message);
                        break;

                    case 'pong':
                        // Pingに対するPong応答 - 無視
                        break;

                    case 'error':
                        this.showMessage(message.message || 'エラーが発生しました', 'error');
                        break;

                    default:
                        console.log('不明なメッセージタイプ:', message.type);
                }
            } catch (error) {
                console.error('メッセージ解析エラー:', error);
            }
        }

        /**
         * 接続更新を処理する
         * @param {Object} message - 接続更新メッセージ
         */
        handleConnectionUpdate(message) {
            if (message.connected !== undefined) {
                this.updateConnectionStatus(message.connected);
                this.updateActivity(message.connected);
            }
        }

        /**
         * コード変更を処理する
         * @param {Object} message - コード変更メッセージ
         */
        handleChordChange(message) {
            if (message.chord) {
                this.updateCurrentChord(message.chord);
                this.renderFretboardDiagram(message.chord);
            }
        }

        /**
         * 練習状態更新を処理する
         * @param {Object} message - 練習更新メッセージ
         */
        handlePracticeUpdate(message) {
            if (message.status) {
                this.practiceStatusText.textContent = message.status;
            }

            if (message.timer) {
                this.timerDisplay.textContent = message.timer;
            }
        }

        /**
         * カメラフレームを受信して表示
         * @param {Object} message - カメラフレームメッセージ
         */
        handleCameraFrame(message) {
            if (!message.data || !this.cameraContext) return;

            const { data, width, height } = message.data;

            // Canvasに画像を描画
            const img = new Image();
            img.onload = () => {
                if (this.cameraCanvas) {
                    this.cameraCanvas.width = width || this.cameraCanvas.width;
                    this.cameraCanvas.height = height || this.cameraCanvas.height;
                    this.cameraContext.drawImage(img, 0, 0, this.cameraCanvas.width, this.cameraCanvas.height);

                    // プレースホルダーを非表示に
                    if (this.cameraPlaceholder) {
                        this.cameraPlaceholder.style.display = 'none';
                    }
                }
            };
            img.src = `data:image/jpeg;base64,${data}`;

            // アクティビティを更新
            this.updateActivity(true);
        }

        /**
         * ゲームモード変更を処理する
         * @param {Object} message - ゲームモードメッセージ
         */
        handleGameMode(message) {
            const mode = message.mode;
            console.log('ゲームモード:', mode);

            // ゲームモードに応じたUI更新
            if (mode === 'game') {
                this.enableGameModeUI();
            } else {
                this.enableFreeModeUI();
            }
        }

        /**
         * ゲーム状態更新を処理する
         * @param {Object} message - ゲーム更新メッセージ
         */
        handleGameUpdate(message) {
            const data = message.data;

            // スコア表示を更新
            const scoreElement = document.getElementById('game-score');
            if (scoreElement && data.score !== undefined) {
                scoreElement.textContent = data.score;
            }

            // コンボ表示を更新
            const comboElement = document.getElementById('game-combo');
            if (comboElement && data.combo !== undefined) {
                comboElement.textContent = data.combo;
            }

            // 統計表示を更新
            if (data.stats) {
                this.updateGameStats(data.stats);
            }
        }

        /**
         * 判定結果を処理する
         * @param {Object} message - 判定メッセージ
         */
        handleJudgement(message) {
            const data = message.data;
            const judgement = data.judgement;

            // 判定表示を更新
            const judgementElement = document.getElementById('game-judgement');
            if (judgementElement) {
                judgementElement.textContent = judgement;
                judgementElement.className = `judgement-display show ${judgement.toLowerCase()}`;

                setTimeout(() => {
                    judgementElement.classList.remove('show');
                }, 500);
            }

            // コンボ表示を更新
            const comboElement = document.getElementById('game-combo');
            if (comboElement && data.combo !== undefined) {
                comboElement.textContent = data.combo;
            }

            // コンボアニメーション
            if (data.combo > 0 && data.combo % 10 === 0) {
                this.showComboAnimation(data.combo);
            }
        }

        /**
         * 接続ステータスを更新する
         * @param {boolean} connected - 接続状態
         */
        updateConnectionStatus(connected) {
            if (connected) {
                this.statusDot.classList.add('connected');
                this.statusText.textContent = '接続中';
            } else {
                this.statusDot.classList.remove('connected');
                this.statusText.textContent = '未接続';
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
         * コントローラーを有効化する
         */
        enableController() {
            if (this.chordSection) {
                this.chordSection.classList.remove('disabled');
            }
            if (this.practiceSection) {
                this.practiceSection.classList.remove('disabled');
            }
            if (this.pairingSection) {
                this.pairingSection.style.display = 'none';
            }
        }

        /**
         * コントローラーを無効化する
         */
        disableController() {
            if (this.chordSection) {
                this.chordSection.classList.add('disabled');
            }
            if (this.practiceSection) {
                this.practiceSection.classList.add('disabled');
            }
            if (this.pairingSection) {
                this.pairingSection.style.display = 'block';
            }
        }

        /**
         * 接続ボタンをリセットする
         */
        resetConnectButton() {
            if (this.connectBtn) {
                this.connectBtn.disabled = false;
                this.connectBtn.textContent = '接続';
            }
        }

        /**
         * コードを選択する
         * @param {string} chordName - コード名
         */
        selectChord(chordName) {
            if (!this.isConnected || !this.ws) {
                this.showMessage('接続されていません', 'error');
                return;
            }

            // 現在のコードと同じ場合は無視
            if (this.currentChord === chordName) {
                return;
            }

            // メッセージを送信
            const message = {
                type: 'chord_change',
                data: { chord: chordName },
                timestamp: Date.now()
            };

            this.ws.send(JSON.stringify(message));
            console.log('コード変更送信:', chordName);

            // UIを更新
            this.updateCurrentChord(chordName);
            this.renderFretboardDiagram(chordName);
        }

        /**
         * 現在のコード表示を更新する
         * @param {string} chordName - コード名
         */
        updateCurrentChord(chordName) {
            this.currentChord = chordName;

            // コード表示を更新
            if (this.currentChordDisplay) {
                this.currentChordDisplay.textContent = chordName;
            }

            // ボタンのアクティブ状態を更新
            document.querySelectorAll('.chord-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.chord === chordName) {
                    btn.classList.add('active');
                }
            });
        }

        /**
         * 練習を開始する
         */
        startPractice() {
            if (!this.isConnected || !this.ws) {
                this.showMessage('接続されていません', 'error');
                return;
            }

            this.isPracticing = true;
            this.practiceStartTime = new Date();

            // メッセージを送信
            const message = {
                type: 'practice_start',
                data: { timestamp: Date.now() }
            };

            this.ws.send(JSON.stringify(message));

            // UIを更新
            this.startPracticeBtn.disabled = true;
            this.stopPracticeBtn.disabled = false;
            this.practiceStatusText.textContent = '練習中...';

            // タイマーを開始
            this.startTimer();
        }

        /**
         * 練習を終了する
         */
        stopPractice() {
            if (!this.isConnected || !this.ws) {
                this.showMessage('接続されていません', 'error');
                return;
            }

            this.isPracticing = false;

            // メッセージを送信
            const message = {
                type: 'practice_end',
                data: { timestamp: Date.now() }
            };

            this.ws.send(JSON.stringify(message));

            // UIを更新
            this.startPracticeBtn.disabled = false;
            this.stopPracticeBtn.disabled = true;
            this.practiceStatusText.textContent = '練習終了';

            // タイマーを停止
            this.stopTimer();
        }

        /**
         * タイマーを開始する
         */
        startTimer() {
            this.stopTimer(); // 既存のタイマーをクリア

            this.timerInterval = setInterval(() => {
                const elapsed = Math.floor((new Date() - this.practiceStartTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                this.timerDisplay.textContent =
                    `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }, 1000);
        }

        /**
         * タイマーを停止する
         */
        stopTimer() {
            if (this.timerInterval) {
                clearInterval(this.timerInterval);
                this.timerInterval = null;
            }
        }

        /**
         * 自動再接続を設定する
         */
        setupAutoReconnect() {
            // 接続が失われた場合の処理は onWebSocketDisconnect で実装済み
        }

        /**
         * メッセージを表示する
         * @param {string} message - 表示するメッセージ
         * @param {string} type - メッセージタイプ（success, error, info）
         */
        showMessage(message, type) {
            if (this.connectionMessage) {
                this.connectionMessage.textContent = message;
                this.connectionMessage.className = `message ${type}`;
            }
        }

        /**
         * 警告を表示する
         * @param {string} message - 警告メッセージ
         */
        showWarning(message) {
            this.showMessage(message, 'info');
        }

        /**
         * ゲームモードUIを有効化する
         */
        enableGameModeUI() {
            // ゲームモード用のUI要素を表示
            const gameStats = document.getElementById('game-stats');
            if (gameStats) {
                gameStats.style.display = 'block';
            }

            const chordSection = document.getElementById('chord-section');
            if (chordSection) {
                chordSection.classList.add('game-mode');
            }
        }

        /**
         * フリーモードUIを有効化する
         */
        enableFreeModeUI() {
            // フリーモード用のUI要素を表示
            const gameStats = document.getElementById('game-stats');
            if (gameStats) {
                gameStats.style.display = 'none';
            }

            const chordSection = document.getElementById('chord-section');
            if (chordSection) {
                chordSection.classList.remove('game-mode');
            }
        }

        /**
         * コンボアニメーションを表示する
         * @param {number} combo - コンボ数
         */
        showComboAnimation(combo) {
            const comboElement = document.getElementById('game-combo');
            if (comboElement) {
                comboElement.classList.add('combo-milestone');
                setTimeout(() => {
                    comboElement.classList.remove('combo-milestone');
                }, 1000);
            }
        }

        /**
         * ゲーム統計を更新する
         * @param {Object} stats - 統計データ
         */
        updateGameStats(stats) {
            const perfectElement = document.getElementById('stat-perfect');
            const greatElement = document.getElementById('stat-great');
            const goodElement = document.getElementById('stat-good');
            const missElement = document.getElementById('stat-miss');

            if (perfectElement) perfectElement.textContent = stats.perfect || 0;
            if (greatElement) greatElement.textContent = stats.great || 0;
            if (goodElement) goodElement.textContent = stats.good || 0;
            if (missElement) missElement.textContent = stats.miss || 0;
        }

        /**
         * クリーンアップ処理
         */
        cleanup() {
            this.stopTimer();

            if (this.ws) {
                this.ws.close();
            }
        }
    }

    // ページ読み込み時に初期化
    document.addEventListener('DOMContentLoaded', function() {
        window.mobileController = new MobileController();
    });

})();
