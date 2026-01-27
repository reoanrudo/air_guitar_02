# Guitar String Sounds

このディレクトリには、ギターの弦の音声ファイルを配置します。

## 現在の実装

現在はWeb Audio APIを使用してリアルタイムに音声を生成しているため、音声ファイルは不要です。

### 実装方法
- `/static/js/guitar.js` でWeb Audio APIを使用
- オシレーターでギター音を合成
- 各弦の周波数:
  - 6弦 (E2): 82.41 Hz
  - 5弦 (A2): 110.00 Hz
  - 4弦 (D2): 146.83 Hz
  - 3弦 (G1): 196.00 Hz
  - 2弦 (B1): 246.94 Hz
  - 1弦 (e1): 329.63 Hz

## 将来的な改善（オプション）

よりリアルなギター音が必要な場合は、以下の方法で音声ファイルを追加できます：

1. 各弦の音声ファイルを用意（MP3またはWAV形式）
2. ファイル名: `string_1.mp3`, `string_2.mp3`, ..., `string_6.mp3`
3. `guitar.js` の `playGuitarSound` 関数を修正して、オーディオファイルを再生するように変更

### オーディオファイルを使用する場合の実装例

```javascript
function playGuitarSound(stringNumber, note) {
    const audio = new Audio(`/static/sounds/strings/string_${stringNumber}.mp3`);

    audio.addEventListener('error', () => {
        console.warn(`音声ファイルの読み込みに失敗しました: string_${stringNumber}.mp3`);
    });

    audio.play().catch(error => {
        console.warn('音声再生に失敗しました:', error);
    });
}
```

## 注意事項

- 音声ファイルを使用する場合、ブラウザの自動再生ポリシーに注意してください
- 各ファイルのサイズは小さく保つことを推奨（圧縮済みMP3で100KB以下）
- 音声ファイルのライセンスに注意してください
