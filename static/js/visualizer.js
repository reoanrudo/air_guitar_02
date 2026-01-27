/**
 * VirtuTune - Audio Visualizer
 *
 * Web Audio APIを使用した音声可視化機能
 */

(function() {
    'use strict';

    // グローバル変数
    let audioContext = null;
    let analyser = null;
    let dataArray = null;
    let canvas = null;
    let canvasCtx = null;
    let isVisualizing = false;
    let animationId = null;

    /**
     * ページ読み込み時の初期化
     */
    document.addEventListener('DOMContentLoaded', function() {
        initializeVisualizer();
        initializeNoteFeedback();
        initializeGoalAchievement();
    });

    /**
     * ビジュアライザーの初期化
     */
    function initializeVisualizer() {
        canvas = document.getElementById('audio-visualizer');
        if (!canvas) {
            console.warn('Audio visualizer canvas not found');
            return;
        }

        canvasCtx = canvas.getContext('2d');
        resizeCanvas();

        // ウィンドウサイズ変更時にキャンバスサイズを調整
        window.addEventListener('resize', resizeCanvas);
    }

    /**
     * キャンバスサイズを調整
     */
    function resizeCanvas() {
        if (!canvas) return;

        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = 200;
    }

    /**
     * Web Audio APIのセットアップ
     * @param {AudioNode} source - 音声ソースノード
     */
    function setupAudioAnalysis(source) {
        // AudioContextの作成（再利用可能な場合は再利用）
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        if (!audioContext) {
            audioContext = new AudioContext();
        }

        // AnalyserNodeの作成
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256; // FFTサイズ（2の累乗である必要あり）

        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        // 音声ソースをアナライザーに接続
        source.connect(analyser);

        // 可視化を開始
        startVisualization();
    }

    /**
     * 可視化を開始
     */
    function startVisualization() {
        if (isVisualizing) return;
        isVisualizing = true;
        draw();
    }

    /**
     * 可視化を停止
     */
    function stopVisualization() {
        isVisualizing = false;
        if (animationId) {
            cancelAnimationFrame(animationId);
            animationId = null;
        }

        // キャンバスをクリア
        if (canvasCtx && canvas) {
            canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
        }
    }

    /**
     * 波形を描画
     */
    function draw() {
        if (!isVisualizing) return;

        animationId = requestAnimationFrame(draw);

        // 周波数データを取得
        analyser.getByteFrequencyData(dataArray);

        // キャンバスをクリア
        canvasCtx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

        // 波形を描画
        const barWidth = (canvas.width / dataArray.length) * 2.5;
        let barHeight;
        let x = 0;

        for (let i = 0; i < dataArray.length; i++) {
            barHeight = (dataArray[i] / 255) * canvas.height;

            // グラデーションカラー
            const gradient = canvasCtx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
            gradient.addColorStop(0, '#667eea');
            gradient.addColorStop(0.5, '#764ba2');
            gradient.addColorStop(1, '#f093fb');

            canvasCtx.fillStyle = gradient;
            canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

            x += barWidth + 1;
        }
    }

    /**
     * 弦が鳴ったときのグローエフェクトを追加
     * @param {HTMLElement} stringElement - 弦の要素
     */
    function addStringGlow(stringElement) {
        stringElement.classList.add('glowing');

        // アニメーション完了後にクラスを削除
        setTimeout(function() {
            stringElement.classList.remove('glowing');
        }, 500);
    }

    /**
     * ノートフィードバックの初期化
     */
    function initializeNoteFeedback() {
        // グローバル関数として公開
        window.showNoteFeedback = showNoteFeedback;
    }

    /**
     * ノートフィードバックを表示
     * @param {string} quality - 'perfect', 'great', 'good', 'miss'
     * @param {number} x - X座標
     * @param {number} y - Y座標
     */
    function showNoteFeedback(quality, x, y) {
        const feedback = document.createElement('div');
        feedback.className = `note-feedback ${quality}`;

        // テキストとスコアの設定
        const config = {
            'perfect': { text: 'Perfect!', score: '+100', color: '#ffd700' },
            'great': { text: 'Great!', score: '+75', color: '#c0c0c0' },
            'good': { text: 'Good', score: '+50', color: '#cd7f32' },
            'miss': { text: 'Miss', score: '+0', color: '#999' }
        };

        const setting = config[quality] || config['miss'];
        feedback.innerHTML = `
            <div class="feedback-text">${setting.text}</div>
            <div class="feedback-score">${setting.score}</div>
        `;

        // 位置の設定
        feedback.style.left = `${x}px`;
        feedback.style.top = `${y}px`;
        feedback.style.color = setting.color;

        // ドキュメントに追加
        document.body.appendChild(feedback);

        // アニメーション完了後に削除
        setTimeout(function() {
            feedback.remove();
        }, 1000);
    }

    /**
     * コンボカウンターを更新
     * @param {number} combo - コンボ数
     */
    function updateComboCounter(combo) {
        let comboDisplay = document.getElementById('combo-counter');
        if (!comboDisplay) {
            comboDisplay = document.createElement('div');
            comboDisplay.id = 'combo-counter';
            comboDisplay.className = 'combo-counter';
            document.body.appendChild(comboDisplay);
        }

        comboDisplay.textContent = `${combo} Combo`;
        comboDisplay.classList.add('combo-animation');

        // アニメーション完了後にクラスを削除
        setTimeout(function() {
            comboDisplay.classList.remove('combo-animation');
        }, 300);
    }

    /**
     * 目標達成エフェクトの初期化
     */
    function initializeGoalAchievement() {
        // グローバル関数として公開
        window.showGoalAchievement = showGoalAchievement;
    }

    /**
     * 目標達成エフェクトを表示
     */
    function showGoalAchievement() {
        // 全画面グラデーションアニメーション
        const overlay = document.createElement('div');
        overlay.className = 'goal-achievement-overlay';
        overlay.innerHTML = `
            <div class="goal-achievement-content">
                <div class="celebration-message">🎉 目標達成！🎉</div>
                <div class="goal-stats">素晴らしい練習です！</div>
            </div>
        `;
        document.body.appendChild(overlay);

        // 紙吹雪エフェクト
        createConfetti();

        // 3秒後に削除
        setTimeout(function() {
            overlay.remove();
        }, 3000);
    }

    /**
     * 紙吹雪エフェクトを作成
     */
    function createConfetti() {
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9d56e', '#ff8b94', '#a8e6cf'];

        for (let i = 0; i < 100; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';

            // ランダムなプロパティ
            const color = colors[Math.floor(Math.random() * colors.length)];
            const left = Math.random() * 100;
            const animationDuration = 2 + Math.random() * 2;
            const size = 5 + Math.random() * 10;

            confetti.style.backgroundColor = color;
            confetti.style.left = `${left}%`;
            confetti.style.animationDuration = `${animationDuration}s`;
            confetti.style.width = `${size}px`;
            confetti.style.height = `${size}px`;

            document.body.appendChild(confetti);

            // アニメーション完了後に削除
            setTimeout(function() {
                confetti.remove();
            }, animationDuration * 1000);
        }
    }

    /**
     * スコアポップアップを表示
     * @param {number} score - スコア
     * @param {number} x - X座標
     * @param {number} y - Y座標
     */
    function showScorePopup(score, x, y) {
        const popup = document.createElement('div');
        popup.className = 'score-popup';
        popup.textContent = `+${score}`;
        popup.style.left = `${x}px`;
        popup.style.top = `${y}px`;

        document.body.appendChild(popup);

        // アニメーション完了後に削除
        setTimeout(function() {
            popup.remove();
        }, 800);
    }

    // グローバル関数として公開
    window.GuitarVisualizer = {
        setupAudioAnalysis: setupAudioAnalysis,
        startVisualization: startVisualization,
        stopVisualization: stopVisualization,
        addStringGlow: addStringGlow,
        updateComboCounter: updateComboCounter,
        showScorePopup: showScorePopup
    };

})();
