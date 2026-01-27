/**
 * VirtuTune - Guitar Page JavaScript with Tone.js
 *
 * 仮想ギター画面のインタラクション処理
 * Tone.jsを使用してリアルなギター音を生成
 */

(function() {
    'use strict';

    // グローバル変数
    let currentChord = null;
    let practiceStartTime = null;
    let timerInterval = null;
    let practicedChords = new Set();
    let comboCount = 0;
    let totalScore = 0;
    let audioInitialized = false;
    let guitarSynths = [];

    // 弦の周波数（標準チューニング）
    const stringFrequencies = {
        '6': 82.41,   // E2
        '5': 110.00,  // A2
        '4': 146.83,  // D2
        '3': 196.00,  // G2
        '2': 246.94,  // B2
        '1': 329.63   // E3 (e1の1オクターブ上)
    };

    /**
     * ページ読み込み時の初期化
     */
    document.addEventListener('DOMContentLoaded', function() {
        initializeGuitar();
        initializeChordSelector();
        initializePracticeControls();
    });

    /**
     * オーディオを初期化（ユーザー操作時に呼ぶ必要あり）
     */
    async function initializeAudio() {
        if (audioInitialized) return;

        try {
            await Tone.start();
            console.log('Tone.js initialized');

            // 各弦のシンセサイザーを作成（リアルなギター音）
            for (let i = 1; i <= 6; i++) {
                const synth = new Tone.Sampler({
                    urls: {
                        C3: "C3.mp3",
                        "D#3": "Ds3.mp3",
                        "F#3": "Fs3.mp3",
                        A3: "A3.mp3",
                    },
                    release: 1,
                    baseUrl: "https://tonejs.github.io/audio/kerero/",
                    onload: () => {
                        console.log(`String ${i} sampler loaded`);
                    }
                }).toDestination();

                // フィードバックとディストーションを追加してギター音に近づける
                const feedback = new Tone.FeedbackDelay("8n.", 0.3, 0.5).toDestination();
                const distortion = new Tone.Distortion(0.2).toDestination();
                synth.connect(distortion);
                synth.connect(feedback);

                guitarSynths[i] = synth;
            }

            audioInitialized = true;
            showNotification('オーディオ準備完了！弦をクリックして音を鳴らしてみましょう！');
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            showNotification('オーディオの初期化に失敗しました。ページをリロードしてください。');
        }
    }

    /**
     * ギター機能の初期化
     */
    function initializeGuitar() {
        // 弦のクリックイベント
        const strings = document.querySelectorAll('.string');
        strings.forEach(string => {
            string.addEventListener('click', async function(e) {
                // 最初のクリックでオーディオを初期化
                if (!audioInitialized) {
                    await initializeAudio();
                }

                const stringNumber = e.target.dataset.string;
                const note = e.target.dataset.note;

                // 弦を鳴らす
                playString(stringNumber, note, e.target);

                // 振動アニメーション
                animateString(e.target);
            });
        });
    }

    /**
     * 弦を鳴らす（Tone.js版）
     * @param {string} stringNumber - 弦の番号
     * @param {string} note - 音符
     * @param {HTMLElement} stringElement - 弦の要素
     */
    function playString(stringNumber, note, stringElement) {
        if (!audioInitialized) {
            showNotification('先に弦をクリックしてオーディオを有効にしてください！');
            return;
        }

        console.log(`String ${stringNumber} (${note}) played`);

        // Tone.jsで音を鳴らす
        const frequency = stringFrequencies[stringNumber];
        if (!frequency) return;

        const synth = guitarSynths[stringNumber];
        if (synth) {
            // 音符を鳴らす
            const midiNote = Tone.Frequency(frequency).toMidi();
            synth.triggerAttackRelease(Tone.Frequency(frequency).toNote(), "8n");
        }

        // グローエフェクトを追加
        addStringGlow(stringElement);

        // ノートフィードバックを表示
        showNoteFeedbackEffect(stringElement);

        // スコア計算
        calculateScore();
    }

    /**
     * 弦にグロー効果を追加
     * @param {HTMLElement} stringElement - 弦の要素
     */
    function addStringGlow(stringElement) {
        stringElement.style.boxShadow = '0 0 20px rgba(255, 215, 0, 0.8)';
        setTimeout(() => {
            stringElement.style.boxShadow = '';
        }, 200);
    }

    /**
     * 弦の振動アニメーション
     * @param {HTMLElement} stringElement - 弦の要素
     */
    function animateString(stringElement) {
        // 振動クラスを追加
        stringElement.classList.add('vibrating');

        // アニメーション完了後にクラスを削除
        setTimeout(function() {
            stringElement.classList.remove('vibrating');
        }, 300);
    }

    /**
     * コードセレクターの初期化
     */
    function initializeChordSelector() {
        const chordButtons = document.querySelectorAll('.chord-btn');

        chordButtons.forEach(button => {
            button.addEventListener('click', async function() {
                // 最初のクリックでオーディオを初期化
                if (!audioInitialized) {
                    await initializeAudio();
                }

                const chordName = this.dataset.chord;
                changeChord(chordName);

                // アクティブクラスの切り替え
                chordButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                // 練習中の場合は記録
                if (practiceStartTime) {
                    practicedChords.add(chordName);
                }

                // コードを鳴らす
                playChord(chordName);
            });
        });
    }

    /**
     * コードを鳴らす
     * @param {string} chordName - コード名
     */
    function playChord(chordName) {
        if (!audioInitialized) return;

        // コードの構成音（簡易版）
        const chordNotes = {
            'C': ['E3', 'C4', 'E4', 'G4'],
            'D': ['A2', 'D3', 'F#3', 'A3'],
            'E': ['E2', 'B2', 'E3', 'G#3', 'B3'],
            'F': ['F2', 'C3', 'F3', 'A3'],
            'G': ['G2', 'D3', 'G3', 'B3'],
            'A': ['A2', 'E3', 'A3', 'C#4'],
            'Am': ['A2', 'C3', 'E3', 'A3'],
            'Em': ['E2', 'G2', 'B2', 'E3'],
        };

        const notes = chordNotes[chordName] || chordNotes['C'];

        // コードをストラム（下から上へ）
        notes.forEach((note, index) => {
            setTimeout(() => {
                // 対応する弦を探して鳴らす
                const stringElement = document.querySelector(`.string[data-note*="${note.charAt(0)}"]`);
                if (stringElement) {
                    const stringNumber = stringElement.dataset.string;
                    playString(stringNumber, note, stringElement);
                    animateString(stringElement);
                }
            }, index * 50); // 50msずつずらしてストローク感を出す
        });
    }

    /**
     * コードを変更する
     * @param {string} chordName - コード名
     */
    function changeChord(chordName) {
        currentChord = chordName;
        const currentChordElement = document.getElementById('current-chord-name');
        currentChordElement.textContent = chordName;

        console.log(`Chord changed to: ${chordName}`);

        // 指板位置の更新を表示
        updateFretboardPositions(chordName);
    }

    /**
     * 指板の押さえる位置を更新
     * @param {string} chordName - コード名
     */
    function updateFretboardPositions(chordName) {
        // まず全てのマーカーをクリア
        document.querySelectorAll('.finger-marker').forEach(m => m.remove());

        // コードの押弦位置（簡易版）
        const chordPositions = {
            'C': [
                { string: 5, fret: 3, finger: 3 },
                { string: 4, fret: 2, finger: 2 },
                { string: 2, fret: 1, finger: 1 },
            ],
            'D': [
                { string: 3, fret: 2, finger: 1 },
                { string: 2, fret: 3, finger: 2 },
                { string: 1, fret: 2, finger: 3 },
            ],
            'E': [
                { string: 3, fret: 1, finger: 1 },
                { string: 2, fret: 2, finger: 3 },
                { string: 1, fret: 1, finger: 1 },
            ],
            'F': [
                { string: 4, fret: 3, finger: 3 },
                { string: 3, fret: 2, finger: 2 },
                { string: 2, fret: 1, finger: 1 },
            ],
            'G': [
                { string: 6, fret: 3, finger: 2 },
                { string: 5, fret: 2, finger: 1 },
            ],
            'A': [
                { string: 4, fret: 2, finger: 2 },
                { string: 3, fret: 2, finger: 2 },
                { string: 2, fret: 2, finger: 2 },
            ],
            'Am': [
                { string: 4, fret: 2, finger: 2 },
                { string: 3, fret: 2, finger: 3 },
                { string: 2, fret: 1, finger: 1 },
            ],
            'Em': [
                { string: 5, fret: 2, finger: 2 },
                { string: 4, fret: 2, finger: 2 },
            ],
        };

        const positions = chordPositions[chordName] || [];

        // 各弦にマーカーを追加
        positions.forEach(pos => {
            const stringElement = document.querySelector(`.string[data-string="${pos.string}"]`);
            if (stringElement) {
                const marker = document.createElement('div');
                marker.className = 'finger-marker';
                marker.innerHTML = `<span class="finger-number">${pos.finger}</span>`;
                marker.style.cssText = `
                    position: absolute;
                    left: ${pos.fret * 60 + 30}px;
                    top: 50%;
                    transform: translateY(-50%);
                    width: 40px;
                    height: 40px;
                    background: rgba(255, 215, 0, 0.8);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 14px;
                    z-index: 10;
                    border: 2px solid #fff;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                `;
                stringElement.appendChild(marker);
            }
        });
    }

    /**
     * 練習コントロールの初期化
     */
    function initializePracticeControls() {
        const startButton = document.getElementById('start-practice');
        const stopButton = document.getElementById('stop-practice');

        startButton.addEventListener('click', startPractice);
        stopButton.addEventListener('click', stopPractice);
    }

    /**
     * 練習を開始する
     */
    function startPractice() {
        if (practiceStartTime) {
            return; // 既に開始している場合は何もしない
        }

        practiceStartTime = new Date();
        practicedChords.clear();

        // タイマーを開始
        timerInterval = setInterval(updateTimer, 1000);

        // ボタンの状態を更新
        document.getElementById('start-practice').disabled = true;
        document.getElementById('stop-practice').disabled = false;

        showNotification('練習を開始しました！頑張りましょう！');
        console.log('Practice started at:', practiceStartTime);
    }

    /**
     * 練習を終了する
     */
    function stopPractice() {
        if (!practiceStartTime) {
            return; // 開始していない場合は何もしない
        }

        // タイマーを停止
        clearInterval(timerInterval);
        timerInterval = null;

        // 練習時間を計算
        const endTime = new Date();
        const duration = Math.floor((endTime - practiceStartTime) / 1000);

        // ボタンの状態を更新
        document.getElementById('start-practice').disabled = false;
        document.getElementById('stop-practice').disabled = true;

        console.log('Practice ended. Duration:', duration, 'seconds');
        console.log('Practiced chords:', Array.from(practicedChords));

        // 変数をリセット
        practiceStartTime = null;

        // 目標達成チェック（5分以上の練習で達成とみなす）
        if (duration >= 300) { // 300秒 = 5分
            showGoalAchievementEffect();
        }

        showNotification(`練習完了！${Math.floor(duration / 60)}分${duration % 60}秒の練習、お疲れ様でした！`);
    }

    /**
     * タイマーを更新する
     */
    function updateTimer() {
        if (!practiceStartTime) {
            return;
        }

        const currentTime = new Date();
        const elapsed = Math.floor((currentTime - practiceStartTime) / 1000);

        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;

        const timerElement = document.getElementById('timer');
        timerElement.textContent =
            String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0');
    }

    /**
     * ノートフィードバックエフェクトを表示
     * @param {HTMLElement} stringElement - 弦の要素
     */
    function showNoteFeedbackEffect(stringElement) {
        // 弦の位置を取得
        const rect = stringElement.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top;

        // ランダムに品質を決定（デモ用）
        const qualities = ['perfect', 'great', 'good', 'miss'];
        const weights = [0.2, 0.3, 0.3, 0.2]; // 良い判定を多くする

        const random = Math.random();
        let quality = 'good';
        let cumulative = 0;

        for (let i = 0; i < weights.length; i++) {
            cumulative += weights[i];
            if (random <= cumulative) {
                quality = qualities[i];
                break;
            }
        }

        // フィードバックを表示
        showNoteFeedback(quality, x, y);
    }

    /**
     * ノートフィードバックを表示
     * @param {string} quality - 品質（perfect, great, good, miss）
     * @param {number} x - X座標
     * @param {number} y - Y座標
     */
    function showNoteFeedback(quality, x, y) {
        const feedback = document.createElement('div');
        feedback.className = `note-feedback feedback-${quality}`;
        feedback.textContent = quality.toUpperCase();

        const qualityTexts = {
            'perfect': 'PERFECT!',
            'great': 'GREAT!',
            'good': 'GOOD',
            'miss': 'MISS...'
        };

        feedback.textContent = qualityTexts[quality] || quality;

        feedback.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y - 50}px;
            transform: translateX(-50%);
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 16px;
            z-index: 1000;
            animation: feedbackPopup 1s ease-out forwards;
        `;

        // 品質によって色を変える
        const colors = {
            'perfect': '#FFD700',
            'great': '#C0C0C0',
            'good': '#CD7F32',
            'miss': '#FF6B6B'
        };
        feedback.style.backgroundColor = colors[quality] || '#333';
        feedback.style.color = quality === 'perfect' || quality === 'great' ? '#000' : '#fff';

        document.body.appendChild(feedback);

        setTimeout(() => {
            feedback.remove();
        }, 1000);
    }

    /**
     * スコアを計算
     */
    function calculateScore() {
        // ランダムにスコアを決定（デモ用）
        const scores = [100, 75, 50, 0];
        const weights = [0.2, 0.3, 0.3, 0.2];

        const random = Math.random();
        let score = 50;
        let cumulative = 0;

        for (let i = 0; i < weights.length; i++) {
            cumulative += weights[i];
            if (random <= cumulative) {
                score = scores[i];
                break;
            }
        }

        // コンボ計算
        if (score > 0) {
            comboCount++;
            totalScore += score;

            // スコアポップアップを表示
            showScorePopup(score);
        } else {
            comboCount = 0;
        }
    }

    /**
     * スコアポップアップを表示
     * @param {number} score - スコア
     */
    function showScorePopup(score) {
        const popup = document.createElement('div');
        popup.className = 'score-popup';
        popup.textContent = `+${score}`;
        popup.style.cssText = `
            position: fixed;
            left: 50%;
            top: 40%;
            transform: translate(-50%, -50%);
            font-size: 32px;
            font-weight: bold;
            color: #FFD700;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
            z-index: 1000;
            animation: scorePopup 0.5s ease-out forwards;
        `;

        document.body.appendChild(popup);

        setTimeout(() => {
            popup.remove();
        }, 500);
    }

    /**
     * 目標達成エフェクトを表示
     */
    function showGoalAchievementEffect() {
        const overlay = document.createElement('div');
        overlay.className = 'goal-achievement-overlay';
        overlay.innerHTML = `
            <div class="goal-achievement-content">
                <div class="trophy">🏆</div>
                <h2>目標達成！</h2>
                <p>5分以上の練習、おめでとうございます！</p>
            </div>
        `;
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            animation: fadeIn 0.5s ease-in;
        `;

        document.body.appendChild(overlay);

        setTimeout(() => {
            overlay.remove();
        }, 3000);

        showNotification('🎉 目標達成！5分以上の練習、おめでとうございます！');
    }

    /**
     * 通知を表示
     * @param {string} message - メッセージ
     */
    function showNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(102, 126, 234, 0.95);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
            z-index: 3000;
            animation: slideIn 0.3s ease-out;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in forwards';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // CSSアニメーションを追加
    const style = document.createElement('style');
    style.textContent = `
        @keyframes feedbackPopup {
            0% { opacity: 0; transform: translateX(-50%) translateY(0); }
            50% { opacity: 1; }
            100% { opacity: 0; transform: translateX(-50%) translateY(-30px); }
        }

        @keyframes scorePopup {
            0% { opacity: 0; transform: translate(-50%, -50%) scale(0.5); }
            50% { opacity: 1; transform: translate(-50%, -50%) scale(1.2); }
            100% { opacity: 0; transform: translate(-50%, -50%) scale(1); }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }

        .goal-achievement-content {
            text-align: center;
            color: white;
        }

        .trophy {
            font-size: 80px;
            margin-bottom: 20px;
        }

        .goal-achievement-content h2 {
            font-size: 36px;
            margin-bottom: 10px;
        }

        .goal-achievement-content p {
            font-size: 18px;
        }
    `;
    document.head.appendChild(style);

    /**
     * WebSocket通信管理（PC側）
     * モバイルコントローラーとのリアルタイム通信
     */
    const PcWebSocketManager = {
        ws: null,
        sessionId: null,
        isConnected: false,
        cameraFrameInterval: null,

        /**
         * WebSocket接続を初期化
         * @param {string} sessionId - セッションID
         */
        async connect(sessionId) {
            if (this.isConnected) {
                console.log('Already connected to WebSocket');
                return;
            }

            this.sessionId = sessionId;

            try {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${wsProtocol}//${window.location.host}/ws/guitar/${sessionId}/`;

                console.log('Connecting to WebSocket:', wsUrl);
                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('PC WebSocket接続確立');
                    this.isConnected = true;
                    this.startCameraFrameBroadcast();
                };

                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocketエラー:', error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket接続終了');
                    this.isConnected = false;
                    this.stopCameraFrameBroadcast();
                };

            } catch (error) {
                console.error('WebSocket接続エラー:', error);
            }
        },

        /**
         * WebSocketメッセージを処理
         * @param {string} data - 受信したJSONデータ
         */
        handleMessage(data) {
            try {
                const message = JSON.parse(data);

                switch (message.type) {
                    case 'connection_update':
                        console.log('接続状態更新:', message.data);
                        break;
                    case 'chord_change':
                        // モバイルからのコード変更を受信
                        if (message.data && message.data.chord) {
                            console.log('Mobile chord change:', message.data.chord);
                            // コード変更を反映（必要に応じて）
                            if (typeof selectChord === 'function') {
                                selectChord(message.data.chord);
                            }
                        }
                        break;
                    case 'practice_update':
                        console.log('練習状態更新:', message.data);
                        break;
                }
            } catch (error) {
                console.error('メッセージ処理エラー:', error);
            }
        },

        /**
         * コード変更をモバイルに送信
         * @param {string} chordName - コード名
         */
        sendChordChange(chordName) {
            if (this.isConnected && this.ws) {
                this.ws.send(JSON.stringify({
                    type: 'chord_change',
                    data: { chord: chordName }
                }));
            }
        },

        /**
         * カメラフレーム配信を開始
         */
        startCameraFrameBroadcast() {
            // 5FPSでカメラフレームを送信
            this.cameraFrameInterval = setInterval(() => {
                this.sendCameraFrame();
            }, 200);
        },

        /**
         * カメラフレーム配信を停止
         */
        stopCameraFrameBroadcast() {
            if (this.cameraFrameInterval) {
                clearInterval(this.cameraFrameInterval);
                this.cameraFrameInterval = null;
            }
        },

        /**
         * カメラフレームを送信
         */
        sendCameraFrame() {
            if (!this.isConnected || !this.ws) return;

            const videoElement = document.getElementById('camera-video');
            if (!videoElement || !videoElement.srcObject) return;

            // Canvasを使ってフレームをキャプチャ
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            // 低解像度でキャプチャ（転送量を削減）
            const width = 320;
            const height = 240;
            canvas.width = width;
            canvas.height = height;

            // ビデオフレームを描画
            ctx.drawImage(videoElement, 0, 0, width, height);

            // JPEG品質0.6でエンコード
            const dataUrl = canvas.toDataURL('image/jpeg', 0.6);

            // base64部分を抽出
            const base64Data = dataUrl.split(',')[1];

            // WebSocketで送信
            this.ws.send(JSON.stringify({
                type: 'camera_frame',
                data: {
                    data: base64Data,
                    width: width,
                    height: height
                }
            }));
        },

        /**
         * WebSocket接続を切断
         */
        disconnect() {
            this.stopCameraFrameBroadcast();
            if (this.ws) {
                this.ws.close();
                this.ws = null;
            }
            this.isConnected = false;
            this.sessionId = null;
        }
    };

    // グローバルスコープに公開
    window.PcWebSocketManager = PcWebSocketManager;

})();
