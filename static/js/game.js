/**
 * リズムゲーム (Rhythm Game)
 *
 * Guitar Hero風のリズムゲームを実装する
 */

class RhythmGame {
    /**
     * コンストラクタ
     * @param {HTMLCanvasElement} canvas - ゲーム描画用キャンバス
     */
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        // ゲーム状態
        this.isPlaying = false;
        this.isPaused = false;
        this.startTime = 0;
        this.lastFrameTime = 0;

        // 楽曲データ
        this.currentSong = null;
        this.notes = [];

        // スコアと統計
        this.score = 0;
        this.combo = 0;
        this.maxCombo = 0;
        this.stats = {
            perfect: 0,
            great: 0,
            good: 0,
            miss: 0
        };

        // タイミング判定基準 (ミリ秒)
        this.timingWindows = {
            perfect: 50,
            great: 100,
            good: 150
        };

        // スコア配分
        this.scoreValues = {
            perfect: 100,
            great: 80,
            good: 60,
            miss: 0
        };

        // ゲーム設定
        this.noteSpeed = 300; // ピクセル/秒
        this.judgmentLineX = 100; // 判定ラインのX座標
        this.hitZone = 50; // ヒットゾーンの幅

        // WebSocket連携
        this.ws = null;
        this.sessionId = null;
        this.currentChord = null;

        // カメラジェスチャー連携
        this.cameraEnabled = false;

        // イベントリスナー
        this.setupEventListeners();
    }

    /**
     * イベントリスナーを設定する
     */
    setupEventListeners() {
        // キーボード入力
        document.addEventListener('keydown', (e) => {
            if (!this.isPlaying) return;

            // コードキー (A-Z)
            if (e.key.match(/^[a-zA-Z]$/)) {
                const chord = e.key.toUpperCase();
                this.handleInput(chord);
            }
        });

        // スペースキーで一時停止/再開
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && this.isPlaying) {
                e.preventDefault();
                this.togglePause();
            }
        });

        // カメラストロームイベント
        window.addEventListener('strum', (e) => {
            if (this.isPlaying && !this.isPaused) {
                this.handleStrum(e.detail.velocity);
            }
        });
    }

    /**
     * WebSocket接続を設定する
     * @param {string} sessionId - セッションID
     */
    setupWebSocket(sessionId) {
        this.sessionId = sessionId;

        if (this.ws) {
            this.ws.close();
        }

        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/mobile/${sessionId}/`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket接続確立 (ゲームモード)');
            this.sendGameMode('game');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocketエラー:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket切断');
        };
    }

    /**
     * WebSocketメッセージを処理する
     * @param {Object} data - 受信したデータ
     */
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'chord_change':
                this.currentChord = data.data.chord;
                this.showCurrentChord(this.currentChord);
                break;

            case 'game_update':
                if (data.data.score !== undefined) {
                    this.syncScore(data.data.score);
                }
                if (data.data.combo !== undefined) {
                    this.syncCombo(data.data.combo);
                }
                break;

            case 'practice_update':
                if (data.data.status === 'started') {
                    this.start(this.currentSong);
                } else if (data.data.status === 'ended') {
                    this.stop();
                }
                break;

            case 'game_pause':
                this.togglePause();
                break;

            default:
                console.log('不明なメッセージタイプ:', data.type);
        }
    }

    /**
     * ゲームモードを送信する
     * @param {string} mode - ゲームモード
     */
    sendGameMode(mode) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'game_mode',
                mode: mode,
                timestamp: Date.now()
            }));
        }
    }

    /**
     * ゲーム状態更新を送信する
     */
    sendGameState() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'game_update',
                data: {
                    score: this.score,
                    combo: this.combo,
                    maxCombo: this.maxCombo,
                    stats: this.stats,
                    timestamp: Date.now()
                }
            }));
        }
    }

    /**
     * カメラストロークを処理する
     * @param {number} velocity - ストローク速度
     */
    handleStrum(velocity) {
        if (!this.isPlaying || this.isPaused) return;

        // カメラが有効な場合、現在のコードでヒット判定
        if (this.cameraEnabled && this.currentChord) {
            this.handleInput(this.currentChord);
        }
    }

    /**
     * カメラを有効化する
     */
    enableCamera() {
        this.cameraEnabled = true;
        console.log('カメラ連携有効化');
    }

    /**
     * カメラを無効化する
     */
    disableCamera() {
        this.cameraEnabled = false;
        console.log('カメラ連携無効化');
    }

    /**
     * 現在のコードを表示する
     * @param {string} chord - コード名
     */
    showCurrentChord(chord) {
        const chordDisplay = document.getElementById('current-chord-display');
        if (chordDisplay) {
            chordDisplay.textContent = chord;
            chordDisplay.classList.add('highlight');
            setTimeout(() => {
                chordDisplay.classList.remove('highlight');
            }, 200);
        }
    }

    /**
     * スコアを同期する
     * @param {number} score - 同期するスコア
     */
    syncScore(score) {
        this.score = score;
        this.updateUI();
    }

    /**
     * コンボを同期する
     * @param {number} combo - 同期するコンボ
     */
    syncCombo(combo) {
        this.combo = combo;
        this.updateUI();
    }

    /**
     * ゲームを開始する
     * @param {Object} songData - 楽曲データ
     */
    start(songData) {
        if (this.isPlaying) {
            this.stop();
        }

        this.currentSong = songData;
        this.notes = this.initializeNotes(songData.notes);
        this.isPlaying = true;
        this.isPaused = false;
        this.startTime = Date.now();
        this.lastFrameTime = this.startTime;

        // 統計をリセット
        this.score = 0;
        this.combo = 0;
        this.maxCombo = 0;
        this.stats = {
            perfect: 0,
            great: 0,
            good: 0,
            miss: 0
        };

        // UIを更新
        this.updateUI();

        // ゲームループを開始
        this.gameLoop();

        // 開始ボタンを非表示
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');
        if (startButton) startButton.style.display = 'none';
        if (stopButton) stopButton.style.display = 'inline-block';
    }

    /**
     * ゲームを停止する
     */
    stop() {
        this.isPlaying = false;
        this.isPaused = false;

        // WebSocket接続をクローズ
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        // 開始ボタンを表示
        const startButton = document.getElementById('startButton');
        const stopButton = document.getElementById('stopButton');
        if (startButton) startButton.style.display = 'inline-block';
        if (stopButton) stopButton.style.display = 'none';

        // 結果を保存して結果画面へ
        this.saveResult();
    }

    /**
     * 一時停止を切り替える
     */
    togglePause() {
        this.isPaused = !this.isPaused;
        if (!this.isPaused) {
            this.lastFrameTime = Date.now();
        }
    }

    /**
     * ノートを初期化する
     * @param {Array} notesData - ノートデータ配列
     * @returns {Array} 初期化されたノート配列
     */
    initializeNotes(notesData) {
        return notesData.map((note, index) => ({
            id: index,
            timing: note.timing,
            note: note.note,
            duration: note.duration || 0.5,
            x: 800, // 画面右端から開始
            y: 200,
            hit: false,
            missed: false
        }));
    }

    /**
     * ゲームループ
     */
    gameLoop() {
        if (!this.isPlaying) return;

        const currentTime = Date.now();
        const deltaTime = (currentTime - this.lastFrameTime) / 1000; // 秒単位
        this.lastFrameTime = currentTime;

        if (!this.isPaused) {
            this.update(deltaTime);
            this.render();
        }

        requestAnimationFrame(() => this.gameLoop());
    }

    /**
     * ゲーム状態を更新する
     * @param {number} deltaTime - 前回フレームからの経過時間（秒）
     */
    update(deltaTime) {
        const gameTime = (Date.now() - this.startTime) / 1000; // 秒単位

        // ノートを更新
        this.updateNotes(deltaTime);

        // ミス判定
        this.checkMissedNotes(gameTime);
    }

    /**
     * ノートを更新する
     * @param {number} deltaTime - 経過時間（秒）
     */
    updateNotes(deltaTime) {
        const gameTime = (Date.now() - this.startTime) / 1000;

        this.notes.forEach(note => {
            if (!note.hit && !note.missed) {
                // 画面右から左へスクロール
                note.x = this.judgmentLineX + (note.timing - gameTime) * this.noteSpeed;

                // 画面外に出たらミス
                if (note.x < -this.hitZone) {
                    note.missed = true;
                    this.handleMiss();
                }
            }
        });

        // ヒットまたはミスしたノートを削除
        this.notes = this.notes.filter(note => !note.hit && !note.missed);
    }

    /**
     * ミスしたノートをチェックする
     * @param {number} gameTime - ゲーム経過時間（秒）
     */
    checkMissedNotes(gameTime) {
        this.notes.forEach(note => {
            if (!note.hit && !note.missed && note.timing < gameTime - 0.5) {
                note.missed = true;
                this.handleMiss();
            }
        });
    }

    /**
     * 入力を処理する
     * @param {string} chord - 入力されたコード
     */
    handleInput(chord) {
        if (!this.isPlaying || this.isPaused) return;

        const gameTime = (Date.now() - this.startTime) / 1000;

        // 判定ライン付近のノートを探す
        const targetNote = this.notes.find(note => {
            if (note.hit || note.missed) return false;

            const timeDiff = Math.abs(note.timing - gameTime) * 1000; // ミリ秒
            const inHitZone = timeDiff <= this.timingWindows.good;

            return inHitZone && note.note === chord;
        });

        if (targetNote) {
            const timeDiff = Math.abs(targetNote.timing - gameTime) * 1000;
            const result = this.checkHit(targetNote, timeDiff);
            this.showJudgement(result.judgement);
        } else {
            // ノートがない場合はミス
            // this.handleMiss();
        }
    }

    /**
     * ヒット判定を行う
     * @param {Object} note - ノートオブジェクト
     * @param {number} timeDiff - タイミングのずれ（ミリ秒）
     * @returns {Object} 判定結果
     */
    checkHit(note, timeDiff) {
        let judgement, score;

        if (timeDiff <= this.timingWindows.perfect) {
            judgement = 'PERFECT';
            score = this.scoreValues.perfect;
            this.stats.perfect++;
        } else if (timeDiff <= this.timingWindows.great) {
            judgement = 'GREAT';
            score = this.scoreValues.great;
            this.stats.great++;
        } else if (timeDiff <= this.timingWindows.good) {
            judgement = 'GOOD';
            score = this.scoreValues.good;
            this.stats.good++;
        } else {
            judgement = 'MISS';
            score = this.scoreValues.miss;
            this.stats.miss++;
            this.combo = 0;
        }

        if (judgement !== 'MISS') {
            note.hit = true;
            this.combo++;
            this.maxCombo = Math.max(this.maxCombo, this.combo);
            this.score += score;
        }

        this.updateUI();

        // WebSocketで判定結果を送信
        this.sendJudgement(judgement, score);

        return { judgement, score };
    }

    /**
     * 判定結果を送信する
     * @param {string} judgement - 判定結果
     * @param {number} score - 獲得スコア
     */
    sendJudgement(judgement, score) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'judgement',
                data: {
                    judgement: judgement,
                    score: score,
                    combo: this.combo,
                    timestamp: Date.now()
                }
            }));
        }
    }

    /**
     * ミスを処理する
     */
    handleMiss() {
        this.stats.miss++;
        this.combo = 0;
        this.showJudgement('MISS');
        this.updateUI();
    }

    /**
     * 判定を表示する
     * @param {string} judgement - 判定結果
     */
    showJudgement(judgement) {
        const display = document.getElementById('judgement');
        if (!display) return;

        display.textContent = judgement;
        display.className = `judgement-display show ${judgement.toLowerCase()}`;

        setTimeout(() => {
            display.classList.remove('show');
        }, 500);
    }

    /**
     * UIを更新する
     */
    updateUI() {
        // スコア
        const scoreElement = document.getElementById('score');
        if (scoreElement) {
            scoreElement.textContent = this.score;
        }

        // コンボ
        const comboElement = document.getElementById('combo');
        if (comboElement) {
            comboElement.textContent = this.combo;
        }

        // 精度
        const accuracyElement = document.getElementById('accuracy');
        if (accuracyElement) {
            const accuracy = this.calculateAccuracy();
            accuracyElement.textContent = `${accuracy.toFixed(1)}%`;
        }

        // WebSocketでゲーム状態を同期
        this.sendGameState();
    }

    /**
     * ゲームを描画する
     */
    render() {
        // キャンバスをクリア
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 判定ラインを描画
        this.renderJudgmentLine();

        // ノートを描画
        this.renderNotes();
    }

    /**
     * 判定ラインを描画する
     */
    renderJudgmentLine() {
        this.ctx.strokeStyle = '#667eea';
        this.ctx.lineWidth = 3;
        this.ctx.beginPath();
        this.ctx.moveTo(this.judgmentLineX, 0);
        this.ctx.lineTo(this.judgmentLineX, this.canvas.height);
        this.ctx.stroke();

        // ヒットゾーン
        this.ctx.fillStyle = 'rgba(102, 126, 234, 0.1)';
        this.ctx.fillRect(
            this.judgmentLineX - this.hitZone,
            0,
            this.hitZone * 2,
            this.canvas.height
        );
    }

    /**
     * ノートを描画する
     */
    renderNotes() {
        this.notes.forEach(note => {
            if (!note.hit && !note.missed) {
                this.renderNote(note);
            }
        });
    }

    /**
     * 個別のノートを描画する
     * @param {Object} note - ノートオブジェクト
     */
    renderNote(note) {
        const x = note.x;
        const y = note.y;
        const radius = 20;

        // ノートの円
        this.ctx.beginPath();
        this.ctx.arc(x, y, radius, 0, Math.PI * 2);

        // 色を設定
        const gradient = this.ctx.createRadialGradient(x, y, 0, x, y, radius);
        gradient.addColorStop(0, '#667eea');
        gradient.addColorStop(1, '#764ba2');

        this.ctx.fillStyle = gradient;
        this.ctx.fill();

        // 枠線
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();

        // コード名
        this.ctx.fillStyle = 'white';
        this.ctx.font = 'bold 14px Arial';
        this.ctx.textAlign = 'center';
        this.ctx.textBaseline = 'middle';
        this.ctx.fillText(note.note, x, y);
    }

    /**
     * スコアを計算する
     * @returns {number} 総スコア
     */
    calculateScore() {
        return (
            this.stats.perfect * this.scoreValues.perfect +
            this.stats.great * this.scoreValues.great +
            this.stats.good * this.scoreValues.good
        );
    }

    /**
     * 精度を計算する
     * @returns {number} 精度（0-1）
     */
    calculateAccuracy() {
        const totalHits = this.stats.perfect + this.stats.great + this.stats.good + this.stats.miss;

        if (totalHits === 0) {
            return 0;
        }

        const weightedScore =
            this.stats.perfect * 1.0 +
            this.stats.great * 0.8 +
            this.stats.good * 0.6;

        return (weightedScore / totalHits) * 100;
    }

    /**
     * 統計情報を取得する
     * @returns {Object} 統計情報
     */
    getStats() {
        return {
            score: this.score,
            maxCombo: this.maxCombo,
            perfectCount: this.stats.perfect,
            greatCount: this.stats.great,
            goodCount: this.stats.good,
            missCount: this.stats.miss,
            accuracy: this.calculateAccuracy()
        };
    }

    /**
     * 結果を保存する
     */
    async saveResult() {
        const stats = this.getStats();

        const data = {
            song_id: this.currentSong.id,
            score: stats.score,
            max_combo: stats.maxCombo,
            perfect_count: stats.perfectCount,
            great_count: stats.greatCount,
            good_count: stats.goodCount,
            miss_count: stats.missCount,
            accuracy: stats.accuracy
        };

        try {
            const response = await fetch('/game/api/save/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const result = await response.json();
                // 結果画面へリダイレクト
                window.location.href = `/game/result/${result.session_id}/`;
            } else {
                console.error('Failed to save game result');
                alert('結果の保存に失敗しました');
            }
        } catch (error) {
            console.error('Error saving game result:', error);
            alert('結果の保存中にエラーが発生しました');
        }
    }

    /**
     * CSRFトークンを取得する
     * @returns {string} CSRFトークン
     */
    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return '';
    }
}

// グローバルスコープでインスタンスを作成
let rhythmGame = null;

// ページ読み込み時に初期化
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('gameCanvas');
    if (canvas) {
        rhythmGame = new RhythmGame(canvas);

        // セッションIDを取得
        const urlParams = new URLSearchParams(window.location.search);
        const sessionId = urlParams.get('session_id');

        if (sessionId) {
            rhythmGame.setupWebSocket(sessionId);
        }

        // カメラ有効化ボタン
        const enableCameraBtn = document.getElementById('enable-camera-btn');
        if (enableCameraBtn) {
            enableCameraBtn.addEventListener('click', () => {
                rhythmGame.enableCamera();
            });
        }

        // カメラ無効化ボタン
        const disableCameraBtn = document.getElementById('disable-camera-btn');
        if (disableCameraBtn) {
            disableCameraBtn.addEventListener('click', () => {
                rhythmGame.disableCamera();
            });
        }

        // スタートボタン
        const startButton = document.getElementById('startButton');
        if (startButton) {
            startButton.addEventListener('click', () => {
                if (typeof songData !== 'undefined') {
                    rhythmGame.start(songData);
                }
            });
        }

        // ストップボタン
        const stopButton = document.getElementById('stopButton');
        if (stopButton) {
            stopButton.addEventListener('click', () => {
                if (rhythmGame) {
                    rhythmGame.stop();
                }
            });
        }
    }
});
