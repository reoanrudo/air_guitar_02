/**
 * VirtuTune - Audio Engine
 *
 * Air Guitar Pro からの移植
 * Tone.js FMシンセサイザーを使用した高品質ギター音声エンジン
 */

(function() {
    'use strict';

    /**
     * AudioEngineクラス
     * Tone.jsを使用したギター音声生成
     * FMシンセサイザー、ディストーション、リバーブを装備
     */
    class AudioEngine {
        constructor() {
            // メインゲイン（音量制御）
            this.mainGain = new Tone.Gain(2.0).toDestination();

            // ディストーションエフェクト
            this.dist = new Tone.Distortion(0.8).connect(this.mainGain);

            // リバーブエフェクト
            this.reverb = new Tone.Reverb({
                decay: 1.5,
                wet: 0.35
            }).connect(this.dist);

            // ローパスフィルター
            this.filter = new Tone.Filter(2500, "lowpass").connect(this.reverb);

            // FMシンセサイザー（ポリフォニック）
            this.synth = new Tone.PolySynth(Tone.FMSynth, {
                harmonicity: 3,
                modulationIndex: 10,
                oscillator: {
                    type: 'sawtooth'
                },
                envelope: {
                    attack: 0.002,  // 鋭いピッキング
                    decay: 0.2,
                    sustain: 0.2,
                    release: 1.2
                }
            }).connect(this.filter);

            // 弦の音階（標準チューニング）
            this.strings = ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'];

            // 初期化状態
            this.isStarted = false;
            this.audioMode = 'mp3'; // 'mp3' or 'fm'
            this.synthVolume = 0.85;
        }

        /**
         * 音声エンジンを初期化
         * Tone.js AudioContextを開始
         */
        async start() {
            if (this.isStarted) return;

            try {
                await Tone.start();
                await Tone.context.resume();
                this.isStarted = true;
                console.log("🎸 Audio Engine: Ready for Rock (FM Synth mode)");
            } catch (e) {
                console.error("Audio Engine failed to start:", e);
                throw e;
            }
        }

        /**
         * MP3サンプラーモード用の初期化
         * 既存のguitar.jsと互換性を持たせるため
         */
        async initMp3Mode() {
            if (this.mp3Synths) return; // 既に初期化済み

            this.mp3Synths = [];

            try {
                await Tone.start();

                // 各弦のサンプラーを作成
                for (let i = 1; i <= 6; i++) {
                    const sampler = new Tone.Sampler({
                        urls: {
                            C3: "C3.mp3",
                            "D#3": "Ds3.mp3",
                            "F#3": "Fs3.mp3",
                            A3: "A3.mp3",
                        },
                        release: 1,
                        baseUrl: "https://tonejs.github.io/audio/kerero/",
                        onload: () => {
                            console.log(`String ${i} sampler loaded (MP3 mode)`);
                        }
                    }).toDestination();

                    // フィードバックとディストーションを追加
                    const feedback = new Tone.FeedbackDelay("8n.", 0.3, 0.5).toDestination();
                    const distortion = new Tone.Distortion(0.2).toDestination();
                    sampler.connect(distortion);
                    sampler.connect(feedback);

                    this.mp3Synths[i] = sampler;
                }

                console.log("🎸 Audio Engine: MP3 mode initialized");
            } catch (error) {
                console.error('Failed to initialize MP3 mode:', error);
            }
        }

        /**
         * ストロークを演奏（FMシンセサイザーモード）
         * @param {number[]} fretStates - 各弦のフレット状態 [弦1, 弦2, ...]
         * @param {string} direction - ストローク方向 'up' または 'down'
         */
        playStrum(fretStates, direction) {
            if (!this.isStarted) return;

            const now = Tone.now();

            // ストローク方向によって弦の順序を変える
            const indices = direction === 'down' ? [0, 1, 2, 3, 4, 5] : [5, 4, 3, 2, 1, 0];

            // 各弦を順番に鳴らす
            indices.forEach((stringIdx, i) => {
                const baseNote = this.strings[stringIdx];
                const fret = fretStates[stringIdx] || 0;

                // フレットに応じて音程をトランスポーズ
                const note = Tone.Frequency(baseNote).transpose(fret).toNote();

                // 弦間の時間差（15ms）でリアルなストローク感を出す
                const strumDelay = i * 0.015;

                // 音を鳴らす
                this.synth.triggerAttackRelease(
                    note,
                    '1n',
                    now + strumDelay,
                    this.synthVolume
                );
            });
        }

        /**
         * MP3モードでのストローク演奏
         * 既存のguitar.jsとの互換性のため
         * @param {number} stringNumber - 弦の番号（1-6）
         * @param {number} frequency - 周波数（Hz）
         */
        playMp3String(stringNumber, frequency) {
            if (!this.mp3Synths || !this.mp3Synths[stringNumber]) return;

            const midiNote = Tone.Frequency(frequency).toMidi();
            this.mp3Synths[stringNumber].triggerAttackRelease(Tone.Frequency(frequency).toNote(), "8n");
        }

        /**
         * ミュート音を演奏
         */
        playMuted() {
            if (!this.isStarted) return;

            // 低い音でミュート感を出す
            this.synth.triggerAttackRelease('E1', '32n', Tone.now(), 0.3);
        }

        /**
         * 音声モードを切り替え
         * @param {string} mode - 'mp3' または 'fm'
         */
        setAudioMode(mode) {
            this.audioMode = mode;
            console.log(`Audio mode changed to: ${mode}`);

            // MP3モードの場合は初期化
            if (mode === 'mp3') {
                this.initMp3Mode();
            }
        }

        /**
         * 音量を設定
         * @param {number} volume - 音量（0.0-1.0）
         */
        setVolume(volume) {
            this.synthVolume = volume;
            this.mainGain.gain.rampTo(volume * 2.0, 0.1);
        }

        /**
         * 現在の音声モードを取得
         */
        getAudioMode() {
            return this.audioMode;
        }

        /**
         * ディストーション量を設定
         * @param {number} amount - ディストーション量（0.0-1.0）
         */
        setDistortion(amount) {
            this.dist.wet.value = amount;
        }

        /**
         * リバーブ量を設定
         * @param {number} amount - リバーブ量（0.0-1.0）
         */
        setReverb(amount) {
            this.reverb.wet.value = amount;
        }
    }

    // グローバルスコープに公開
    window.AudioEngine = AudioEngine;

})();
