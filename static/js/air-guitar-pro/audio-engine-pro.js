/**
 * Audio Engine Pro
 *
 * Tone.jsを使用したギター音声エンジン
 *
 * 機能:
 * - FMシンセサイザーによるギター音合成
 * - エフェクトチェーン（Distortion → Reverb → Filter → Gain）
 * - ポリフォニックシンセ（6音同時発音可能）
 * - ストローク方向による弦の順序制御
 * - ミュート音
 * - 音量・エフェクト調整
 */

class AudioEnginePro {
  constructor() {
    console.log('AudioEnginePro: Initializing');

    // メインゲイン（音量制御）
    this.mainGain = new Tone.Gain(2.0).toDestination();
    console.log('AudioEnginePro: Main gain connected');

    // ディストーションエフェクト
    this.dist = new Tone.Distortion(0.8).connect(this.mainGain);
    console.log('AudioEnginePro: Distortion connected');

    // リバーブエフェクト
    this.reverb = new Tone.Reverb({
      decay: 1.5,
      wet: 0.35
    }).connect(this.dist);
    console.log('AudioEnginePro: Reverb connected');

    // ローパスフィルター
    this.filter = new Tone.Filter(2500, 'lowpass').connect(this.reverb);
    console.log('AudioEnginePro: Filter connected');

    // FMシンセサイザー（ポリフォニック）
    this.synth = new Tone.PolySynth(Tone.FMSynth, {
      harmonicity: 3,
      modulationIndex: 10,
      oscillator: { type: 'sawtooth' },
      envelope: {
        attack: 0.002,  // 鋭いピッキング
        decay: 0.2,
        sustain: 0.2,
        release: 1.2
      }
    }).connect(this.filter);
    console.log('AudioEnginePro: FM Synth connected');

    // 弦の音階（標準チューニング）
    this.strings = ['E2', 'A2', 'D3', 'G3', 'B3', 'E4'];

    // 初期化状態
    this.isStarted = false;
    this.synthVolume = 0.85;

    console.log('AudioEnginePro: Initialization complete');
  }

  async start() {
    if (this.isStarted) {
      console.log('AudioEnginePro: Already started');
      return;
    }

    try {
      await Tone.start();
      await Tone.context.resume();
      this.isStarted = true;
      console.log("🎸 Audio Engine: Ready for Rock");
    } catch (e) {
      console.error("Audio Engine failed to start:", e);
      throw e;
    }
  }

  playStrum(fretStates, direction) {
    if (!this.isStarted) {
      console.warn('AudioEnginePro: Not started, ignoring playStrum');
      return;
    }

    const now = Tone.now();
    const indices = direction === 'down' ? [0, 1, 2, 3, 4, 5] : [5, 4, 3, 2, 1, 0];

    console.log(`AudioEnginePro: Playing strum. Frets: [${fretStates.join(', ')}], Direction: ${direction}`);

    indices.forEach((stringIdx, i) => {
      const baseNote = this.strings[stringIdx];
      const fret = fretStates[stringIdx] || 0;

      // フレットに応じて音程をトランスポーズ
      const note = Tone.Frequency(baseNote).transpose(fret).toNote();

      // 弦間の時間差でリアルなストローク感を出す
      const strumDelay = i * 0.015; // 15ms per string

      this.synth.triggerAttackRelease(note, '1n', now + strumDelay, this.synthVolume);
    });
  }

  playMuted() {
    if (!this.isStarted) {
      console.warn('AudioEnginePro: Not started, ignoring playMuted');
      return;
    }

    console.log('AudioEnginePro: Playing muted note');
    this.synth.triggerAttackRelease('E1', '32n', Tone.now(), 0.3);
  }

  setVolume(volume) {
    this.synthVolume = volume;
    console.log(`AudioEnginePro: Volume set to ${volume}`);
    this.mainGain.gain.rampTo(volume * 2.0, 0.1);
  }

  setDistortion(amount) {
    this.dist.wet.value = amount;
    console.log(`AudioEnginePro: Distortion set to ${amount}`);
  }

  setReverb(amount) {
    this.reverb.wet.value = amount;
    console.log(`AudioEnginePro: Reverb set to ${amount}`);
  }
}
