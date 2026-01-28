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
    
    // 音声エンジン（AudioEngine）
    const audioEngine = null;

    // パーティクルシステム
    const particleSystem = null;

    /**
     * ページ読み込み時の初期化
     */
    document.addEventListener('DOMContentLoaded', function() {
        initializeGuitar();
        initializeChordSelector();
        initializePracticeControls();
        initializeAudioSettings();
        initializeParticleSystem();
        initializeLeftHandFretboard();
    });

    /**
     * オーディオを初期化（ユーザー操作時に呼ぶ必要あり）
     */
    async function initializeAudio() {
        if (audioInitialized) return;

        try {
            // AudioEngine を初期化（新しい FM シンセサイザー）
            console.log('Audio Engine initializing...');
            audioEngine = new AudioEngine();
            
            // デフォルトはFMシンセサイザーーモード（高品質）
            await audioEngine.start();
            
            audioInitialized = true;
            console.log('Audio Engine ready:', audioEngine);
            
            // 音声設定 UI から AudioEngine を設定
            updateAudioEngineSettings();
            
            showNotification('オーディオ準備完了！FMシンセサイザーで高品質ギター音');
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            showNotification('オーディオの初期化に失敗しました。ページをリロードしてください。');
        }
    }

    /**
     * 音声設定を Audio Engine に転送
     */
    function updateAudioEngineSettings() {
        if (!audioEngine) return;

        // 音声モードボタンのクリックイベントを監視
        const modeButtons = document.querySelectorAll('.audio-mode-btn');
        const volumeSlider = document.getElementById('audio-volume');
        const volumeValue = document.querySelector('.volume-value');

        if (modeButtons.length === 0 || !volumeSlider || !volumeValue) {
            console.warn('Audio settings UI elements not found');
            return;
        }

        modeButtons.forEach(btn => {
            btn.addEventListener('click', function() {
                const mode = this.dataset.mode;
                if (!audioInitialized) {
                    initializeAudio();
                }

                audioEngine.setAudioMode(mode);

                modeButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                console.log(`Audio mode changed to: ${mode}`);
            });
        });

        // 音量スライダーのリアルタイム更新
        if (volumeSlider && volumeValue) {
            volumeSlider.addEventListener('input', function() {
                const value = this.value;
                volumeValue.textContent = `${value}%`;

                if (audioInitialized) {
                    audioEngine.setVolume(value / 100);
                }

                // リアルタイムで音量を変更（即時反映なし）
                audioEngine.mainGain.gain.rampTo(value / 50, 0.1);
            });
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
     * フィードバックを表示（ヒットゾーンではなく、弦の位置に表示）
         * @param {HTMLElement} stringElement - 弦の要素
         */
        function showNoteFeedbackEffect(stringElement) {
        // 弦の位置を取得
        const rect = stringElement.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        // ランダムに品質を決定（デモ用）
        const qualities = ['perfect', 'great', 'good', 'miss'];
        const weights = [0.2, 0.3, 0.3, 0.2];

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

        // フィードバックを表示（ヒットゾーンではなく、弦の位置に表示）
        showNoteFeedback(quality, x, y);

        // パーティクルを生成
        if (particleSystem) {
            if (quality === 'perfect') {
                particleSystem.spawnHitParticles(x, y);
            } else if (quality === 'great') {
                particleSystem.spawnHitParticles(x, y);
            }
        }

        // 左手モード：単音
        const leftChord = getCurrentChordName();

        // 左手コードボードのフレット位置を更新
        if (leftChord && leftChord !== '-') {
            updateFretboardPositions(leftChord);
        }
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

                    // パーティクルを生成
                    if (particleSystem) {
                        const rect = stringElement.getBoundingClientRect();
                        particleSystem.spawnHitParticles(rect.left + rect.width / 2, rect.top);
                    }
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
     * 音声設定の初期化
     */
    function initializeAudioSettings() {
        const modeButtons = document.querySelectorAll('.audio-mode-btn');
        const volumeSlider = document.getElementById('audio-volume');
        const volumeValue = document.querySelector('.volume-value');

        modeButtons.forEach(btn => {
            btn.addEventListener('click', async function() {
                const mode = this.dataset.mode;

                if (!audioInitialized) {
                    await initializeAudio();
                }

                audioEngine.setAudioMode(mode);

                modeButtons.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                console.log(`Audio mode changed to: ${mode}`);
            });
        });

        volumeSlider.addEventListener('input', function() {
            const value = this.value;
            volumeValue.textContent = `${value}%`;
            audioEngine.setVolume(value / 100);

            if (audioInitialized) {
                audioEngine.mainGain.gain.rampTo(value / 50, 0.1);
            }
        });
    }

    /**
     * パーティクルシステムの初期化
     */
    function initializeParticleSystem() {
        const canvas = document.getElementById('particle-canvas');
        if (canvas && window.ParticleSystem) {
            particleSystem = new ParticleSystem();
            particleSystem.initializeCanvas(canvas);
            particleSystem.start();
        }
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

    // コンボカウンターのアニメーション
    function animateCombo(combo) {
        const comboCounter = document.querySelector('.combo-counter');
        if (!comboCounter) return;

        // コンボクラスを追加/削除してアニメーション
        comboCounter.classList.remove('combo-animation');
        
        // アニメーションを再トリガー
        void comboCounter.offsetWidth;
        comboCounter.classList.add('combo-animation');
    }

    /**
     * 左手コードボードの初期化
     */
    function initializeLeftHandFretboard() {
        const grid = document.getElementById('left-hand-fretboard-grid');
        if (!grid) return;

        // モードセレクターを取得
        const modePcBtn = document.getElementById('mode-pc');
        const modeMobileBtn = document.getElementById('mode-mobile');

        // 弦名とフレット数
        const stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];
        const fretCount = 4;

        // 各弦の行を生成
        stringNames.forEach((name, stringIdx) => {
            const row = document.createElement('div');
            row.className = 'string-row';
            row.innerHTML = `<span class="string-label-fretboard">${stringNames[stringIdx]}弦</span>`;

            // 弦上の開弦エリア（ミュート状態）
            const openStringZone = document.createElement('div');
            openStringZone.className = 'fret-zone';
            openStringZone.setAttribute('data-string', stringIdx);
            openStringZone.setAttribute('data-fret', '0');
            openStringZone.onclick = () => handleFretTouch(stringIdx, 0);
            row.appendChild(openStringZone);

            // 各フレットのゾーン
            for (let fretIdx = 1; fretIdx <= fretCount; fretIdx++) {
                const fretZone = document.createElement('div');
                fretZone.className = 'fret-zone';
                fretZone.setAttribute('data-string', stringIdx);
                fretZone.setAttribute('data-fret', fretIdx);
                fretZone.onclick = () => handleFretTouch(stringIdx, fretIdx);
                fretZone.innerHTML = `<span class="fret-number">${fretIdx}</span>`;
                row.appendChild(fretZone);
            }

            grid.appendChild(row);
        });
    }

    /**
     * モード切り替えイベント
     */
    if (modePcBtn && modeMobileBtn) {
        modePcBtn.addEventListener('click', function() {
            modePcBtn.classList.add('active');
            modeMobileBtn.classList.remove('active');
            currentHandMode = 'pc';
            console.log('Mode switched to: PC操作');
        });

        modeMobileBtn.addEventListener('click', function() {
            modePcBtn.classList.remove('active');
            modeMobileBtn.classList.add('active');
            currentHandMode = 'mobile';
            console.log('Mode switched to: スマホ操作');
        });
    }

            grid.appendChild(row);
        });
    }

    /**
     * 左手コードボードの初期化（簡易版）
     */
    function initializeLeftHandFretboard() {
        const grid = document.getElementById('left-hand-fretboard-grid');
        if (!grid) return;

        // 弦名とフレット数
        const stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];
        const fretCount = 4;

        // 各弦の行を生成
        stringNames.forEach((name, stringIdx) => {
            const row = document.createElement('div');
            row.className = 'string-row';
            row.innerHTML = `<span class="string-label-fretboard">${stringNames[stringIdx]}弦</span>`;

            // 開弦（左手でミュートする弦）
            const openStringZone = document.createElement('div');
            openStringZone.className = 'fret-zone';
            openStringZone.setAttribute('data-string', stringIdx);
            openStringZone.setAttribute('data-fret', '0');
            openStringZone.onclick = () => handleFretTouch(stringIdx, 0);
            row.appendChild(openStringZone);

            // 各フレットのゾーン
            for (let fretIdx = 1; fretIdx <= fretCount; fretIdx++) {
                const fretZone = document.createElement('div');
                fretZone.className = 'fret-zone';
                fretZone.setAttribute('data-string', stringIdx);
                fretZone.setAttribute('data-fret', fretIdx);
                fretZone.onclick = () => handleFretTouch(stringIdx, fretIdx);
                fretZone.innerHTML = `<span class="fret-number">${fretIdx}</span>`;
                row.appendChild(fretZone);
            }

            grid.appendChild(row);
        });
    }

            grid.appendChild(row);
        });
    }

    /**
     * 左手コードボードの初期化（簡易版）
     */
    function initSimpleLeftHandFretboard() {
        const grid = document.getElementById('left-hand-fretboard-grid');
        if (!grid) return;

        const stringNames = ['E', 'A', 'D', 'G', 'B', 'E'];
        const fretCount = 4;

        stringNames.forEach((name, stringIdx) => {
            const row = document.createElement('div');
            row.className = 'string-row';
            row.innerHTML = `<span class="string-label-fretboard">${stringNames[stringIdx]}弦</span>`;

            // 弦上の開弦エリア（ミュートする弦）
            const openStringZone = document.createElement('div');
            openStringZone.className = 'fret-zone';
            openStringZone.setAttribute('data-string', stringIdx);
            openStringZone.setAttribute('data-fret', '0');
            openStringZone.onclick = () => handleFretTouch(stringIdx, 0);
            row.appendChild(openStringZone);

            for (let fretIdx = 1; fretIdx <= fretCount; fretIdx++) {
                const fretZone = document.createElement('div');
                fretZone.className = 'fret-zone';
                fretZone.setAttribute('data-string', stringIdx);
                fretZone.setAttribute('data-fret', fretIdx);
                fretZone.onclick = () => handleFretTouch(stringIdx, fretIdx);
                fretZone.innerHTML = `<span class="fret-number">${fretIdx}</span>`;
                row.appendChild(fretZone);
            }

            grid.appendChild(row);
        });
    }

    /**
     * フレットタッチイベント（左手コードボード用）
     */
    function handleFretTouch(stringIdx, fret) {
        if (!audioInitialized) {
            initializeAudio();
        }

        // タッチ振動フィードバック
        if (window.navigator.vibrate) {
            window.navigator.vibrate(10);
        }

        // 弦を鳴らす（左手用：単音）
        const fretStates = new Array(6).fill(0);
        fretStates[stringIdx] = fret;

        // PCに送信（左手用コードイベント）
        const chordData = {
            name: getCurrentChordName() || '-',
            position: 'left_hand'
        };

        if (audioEngine) {
            audioEngine.playStrum(fretStates, 'down');
        }

        // パーティクルを生成
        if (particleSystem) {
            const rect = touchedZone.getBoundingClientRect();
            particleSystem.spawnStrumParticles(rect.left + rect.width / 2, rect.top + rect.height / 2);
        }
    }

        // タッチ振動フィードバック
        if (window.navigator.vibrate) {
            window.navigator.vibrate(10);
        }

        // アクティブ状態を更新
        const allZones = document.querySelectorAll(`[data-string="${stringIdx}"]`);
        allZones.forEach(zone => {
            if (zone.classList.contains('active')) {
                zone.classList.remove('active');
            }
        });

        const touchedZone = document.querySelector(`[data-string="${stringIdx}"][data-fret="${fret}"]`);
        if (touchedZone) {
            touchedZone.classList.add('active');
        }

        // 弦を鳴らす（左手用：単音）
        const fretStates = new Array(6).fill(0);
        fretStates[stringIdx] = fret;

        // PCに送信（左手用コードイベント）
        const chordData = {
            name: getCurrentChordName() || '-',
            position: 'left_hand'
        };

        if (audioEngine) {
            audioEngine.playStrum(fretStates, 'down');
        }

        // WebSocketでPCに送信
        sendWebSocketMessage('chord_change', chordData);

        // パーティクルを生成
        if (particleSystem) {
            const rect = touchedZone.getBoundingClientRect();
            particleSystem.spawnStrumParticles(rect.left + rect.width / 2, rect.top + rect.height / 2);
        }
    }

            grid.appendChild(row);
        });
    }

    /**
     * フレットタッチ/クリックイベント
     */
    function handleFretTouch(stringIdx, fret) {
        if (!audioInitialized) {
            initializeAudio();
        }

        // タッチ振動フィードバック
        if (window.navigator.vibrate) {
            window.navigator.vibrate(10);
        }

        // アクティブ状態を更新
        const allZones = document.querySelectorAll(`[data-string="${stringIdx}"]`);
        allZones.forEach(zone => {
            if (zone.classList.contains('active')) {
                zone.classList.remove('active');
            }
        });

        const touchedZone = document.querySelector(`[data-string="${stringIdx}"][data-fret="${fret}"]`);
        if (touchedZone) {
            touchedZone.classList.add('active');
        }

        // 弦を鳴らす（左手用：単音）
        const fretStates = new Array(6).fill(0);
        fretStates[stringIdx] = fret;

        if (audioEngine) {
            audioEngine.playStrum(fretStates, 'down');
        }

        // パーティクルを生成
        if (particleSystem) {
            const rect = touchedZone.getBoundingClientRect();
            particleSystem.spawnStrumParticles(rect.left + rect.width / 2, rect.top + rect.height / 2);
        }
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
     * フレットボード位置の更新（左手コード用）
     * @param {string} chordName - コード名
     */
    function updateFretboardPositions(chordName) {
        // 左手コードの位置定義（Air Guitar Pro から採用）
        const chordPatterns = {
            'C': [0, 1, 0, 2, 3, 0],
            'G': [3, 0, 0, 0, 2, 3],
            'D': [2, 3, 2, 0, 0, 0, 2],
            'Am': [0, 1, 2, 2, 0, 0, 0],
            'F': [1, 1, 2, 0, 0, 0, 0],
            'E': [0, 1, 2, 0, 0, 0, 0],
            'A': [0, 0, 1, 2, 0, 0, 0],
            'Em': [0, 2, 2, 0, 0, 0, 2]
        };

        const positions = chordPatterns[chordName] || [];

        document.querySelectorAll('.finger-marker').forEach(marker => {
            const posParts = marker.dataset.pos.split(',');
            const stringIdx = parseInt(marker.dataset.string);
            const fret = parseInt(marker.dataset.fret);
            const finger = marker.innerHTML;

            // 既存のフォーマット（"string,fret"）を維持
            const existingPositions = positions[finger] || new Set();

            // 新しい位置を設定
            existingPositions.add(`${stringIdx},${fret}`);

            marker.innerHTML = finger;
        });

        return positions;
    }
        }

        // フィードバックを表示（ヒットゾーンではなく、弦の位置に表示）
        showNoteFeedback(quality, x, y);

        // パーティクルを生成
        if (particleSystem) {
            if (quality === 'perfect') {
                particleSystem.spawnHitParticles(x, y);
            } else if (quality === 'great') {
                particleSystem.spawnHitParticles(x, y);
            }
        }

        // 弦の発光エフェクトを追加
        if (stringElement) {
            stringElement.classList.add('strummed');
            setTimeout(() => {
                stringElement.classList.remove('strummed');
            }, 200);
        }
    }
        }

        // フィードバックを表示（ヒットゾーンではなく、弦の位置に表示）
        showNoteFeedback(quality, x, y);

        // パーティクルを生成
        if (particleSystem) {
            if (quality === 'perfect') {
                particleSystem.spawnHitParticles(x, y);
            } else if (quality === 'great') {
                particleSystem.spawnHitParticles(x, y);
            }
        }
    }
        }

         // フィードバックを表示
         showNoteFeedback(quality, x, y);

        // パーティクルを生成
        if (particleSystem) {
            if (quality === 'perfect') {
                particleSystem.spawnHitParticles(x, y);
            } else if (quality === 'great') {
                particleSystem.spawnHitParticles(x, y);
            }
        }
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
            top: ${y}px;
            transform: translateX(-50%);
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 16px;
            z-index: 1000;
        `;

        document.body.appendChild(feedback);

        // 適切なタイミングで削除
        const duration = quality === 'perfect' ? 3000 : 500;
        setTimeout(() => {
            feedback.remove();
        }, duration);
    }

    /**
     * スコアを計算
     */
    function calculateScore() {
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

            // コンボカウンターのアニメーションを追加
            animateCombo(comboCount);

            // コンボマイルストーン時のパーティクル
            if (comboCount > 0 && comboCount % 5 === 0) {
                const comboDisplay = document.querySelector('.combo-counter');
                if (comboDisplay) {
                    const rect = comboDisplay.getBoundingClientRect();
                    if (particleSystem) {
                        particleSystem.spawnComboParticles(rect.left + rect.width / 2, rect.top, comboCount);
                    }
                }
            }
        } else {
            comboCount = 0;
        }
    }

    /**
     * フレットボード位置の更新
     * @param {string} chordName - コード名
     */
    function updateFretboardPositions(chordName) {
        const fingerMarkers = {
            'C': [
                { string: 3, fret: 0, finger: 2 },
                { string: 2, fret: 0, finger: 1 },
                { string: 4, fret: 0, finger: 1 },
                { string: 5, fret: 2, finger: 3 }
            ],
            'G': [
                { string: 6, fret: 3, finger: 2 },
                { string: 5, fret: 3, finger: 3 },
                { string: 6, fret: 2, finger: 4 },
                { string: 5, fret: 2, finger: 4 }
            ],
            'D': [
                { string: 4, fret: 1, finger: 1 },
                { string: 3, fret: 2, finger: 2 },
                { string: 4, fret: 3, finger: 2 },
                { string: 5, fret: 1, finger: 3 }
            ],
            'Am': [
                { string: 0, fret: 2, finger: 2 },
                { string: 1, fret: 1, finger: 1 },
                { string: 2, fret: 2, finger: 2 },
                { string: 3, fret: 2, finger: 2 }
            ],
            'F': [
                { string: 1, fret: 0, finger: 1 },
                { string: 2, fret: 0, finger: 2 },
                { string: 3, fret: 0, finger: 2 },
                { string: 4, fret: 0, finger: 3 },
                { string: 5, fret: 1, finger: 3 }
            ],
            'E': [
                { string: 4, fret: 1, finger: 1 },
                { string: 5, fret: 1, finger: 1 },
                { string: 6, fret: 1, finger: 1 }
            ],
            'Em': [
                { string: 0, fret: 2, finger: 1 },
                { string: 1, fret: 2, finger: 2 },
                { string: 2, fret: 2, finger: 2 }
            ],
            '-': [
                { string: 1, fret: 0, finger: 0 }
            ]
        };

        const positions = fingerMarkers[chordName] || [];

        document.querySelectorAll('.finger-marker').forEach(marker => {
            marker.remove();
        });

        // フレットボードのマーカーを更新
        document.querySelectorAll('.fret-zone').forEach(zone => {
            zone.innerHTML = '';
            positions.forEach(pos => {
                if (pos.string === zone.dataset.string && pos.fret === zone.dataset.fret) {
                    zone.innerHTML = `<span class="finger-marker">${pos.finger}</span>`;
                }
            });
    }

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
            color: #ffd700;
            text-shadow: 0 0 10px rgba(255, 215, 0, 0.8);
            z-index: 1000;
            animation: score-popup-animation 0.8s ease-out forwards;
        `;

        document.body.appendChild(popup);

        // アニメーション完了後に削除
        setTimeout(() => {
            popup.remove();
        }, 800);
    }

    /**
     * コンボカウンターのアニメーション
     * @param {number} combo - コンボ数
     */
    function animateCombo(combo) {
        const comboCounter = document.querySelector('.combo-counter');
        if (!comboCounter) return;

        // コンボクラスを追加/削除してアニメーション
        comboCounter.classList.remove('combo-animation');
        
        // アニメーションを再トリガー
        void comboCounter.offsetWidth;
        comboCounter.classList.add('combo-animation');
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
