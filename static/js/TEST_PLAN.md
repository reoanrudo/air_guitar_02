# 仮想ギターJavaScript機能 - テスト計画

## 実装済み機能

### 1. 弦のクリックイベント
- [x] すべての弦（1-6弦）にクリックイベントリスナーを追加
- [x] クリック時に音声再生と振動アニメーションをトリガー
- [x] data-string属性とdata-note属性を正しく取得

### 2. 音声再生（Web Audio API）
- [x] Web Audio APIを使用したリアルタイム音声生成
- [x] 各弦に適切な周波数を設定:
  - 6弦 (E2): 82.41 Hz
  - 5弦 (A2): 110.00 Hz
  - 4弦 (D2): 146.83 Hz
  - 3弦 (G1): 196.00 Hz
  - 2弦 (B1): 246.94 Hz
  - 1弦 (e1): 329.63 Hz
- [x] 三角波オシレーターでギター風の音質を実現
- [x] アタックとディケイのエンベロープ制御
- [x] ブラウザ互換性対応（webkitAudioContext）
- [x] メモリリーク防止のための適切なクリーンアップ
- [x] Web Audio API非対応ブラウザの場合のグラデュアルデグラデーション

### 3. 弦の振動アニメーション
- [x] CSS keyframeアニメーションを実装（`vibrate`）
- [x] JavaScriptで `vibrating` クラスを追加/削除
- [x] アニメーション設定: 0.1秒 × 3回繰り返し（合計0.3秒）
- [x] アニメーション完了後にクラスを自動削除
- [x] 視覚的フィードバック（金色の光沢効果）

### 4. コード切り替え
- [x] コードボタンクリックで現在のコードを更新
- [x] 選択されたコードボタンをハイライト（`active`クラス）
- [x] 現在のコード名を表示
- [x] 練習中に使用したコードをSetで追跡
- [x] currentChord変数で現在のコードを保存

### 5. 練習タイマー統合
- [x] 「練習開始」ボタンでタイマー開始
- [x] 「練習終了」ボタンでタイマー停止
- [x] 1秒ごとにタイマー表示を更新（MM:SS形式）
- [x] 練習中のコードをpracticedChords Setで追跡
- [x] ボタンのdisabled状態を適切に制御
- [x] 練習終了時に所要時間と練習したコードをログ出力

## テスト手順

### 手動テスト

1. **ギター画面の表示**
   ```bash
   # Django開発サーバーを起動
   python manage.py runserver

   # ブラウザで以下のURLにアクセス
   http://localhost:8000/guitar/
   ```

2. **弦のクリックテスト**
   - 各弦（1-6弦）をクリック
   - 確認事項:
     - [ ] 音が鳴る（ギター風の音）
     - [ ] 弦が振動するアニメーションが見える
     - [ ] コンソールに `"String X (note) played"` とログが出る
     - [ ] アニメーションが0.3秒で終了する

3. **コード切り替えテスト**
   - コードボタンをクリック
   - 確認事項:
     - [ ] クリックしたボタンがハイライトされる
     - [ ] 「現在のコード」表示が更新される
     - [ ] 他のボタンのハイライトが解除される

4. **練習タイマーテスト**
   - 「練習開始」ボタンをクリック
   - 確認事項:
     - [ ] タイマーがカウントアップを開始
     - [ ] 「練習開始」ボタンが無効化される
     - [ ] 「練習終了」ボタンが有効化される
     - [ ] コードを切り替えると、そのコードが記録される

   - 「練習終了」ボタンをクリック
   - 確認事項:
     - [ ] タイマーが停止する
     - [ ] コンソールに練習時間と練習したコードが出力される
     - [ ] 「練習開始」ボタンが再有効化される
     - [ ] 「練習終了」ボタンが無効化される

5. **ブラウザ互換性テスト**
   - Chrome, Firefox, Safari, Edgeでテスト
   - 確認事項:
     - [ ] すべてのブラウザで音声が再生される
     - [ ] アニメーションがスムーズに動作する

### 自動テスト（将来の実装）

```javascript
// TODO: JavaScript単体テストの追加
// テストフレームワーク: Jest または Mocha

describe('Guitar', () => {
    test('should play sound when string is clicked', () => {
        // テスト実装
    });

    test('should animate string vibration', () => {
        // テスト実装
    });

    test('should change chord when button is clicked', () => {
        // テスト実装
    });

    test('should start and stop timer correctly', () => {
        // テスト実装
    });
});
```

## 既知の制限事項

1. **オーディオファイルの代替**
   - 現在はWeb Audio APIで音声を合成しているため、リアルなギター音ではない
   - 将来的にオーディオファイルを使用する場合は、`playGuitarSound`関数を修正

2. **ブラウザの自動再生ポリシー**
   - 一部のブラウザでは、ユーザー操作なしに音声を再生できない場合がある
   - 最初の弦クリックでAudioContextを初期化しているため、問題はないはず

3. **モバイルデバイス**
   - モバイルブラウザでのWeb Audio APIの挙動を確認する必要がある

## パフォーマンス考慮事項

- [x] AudioContextを適切にクローズしてメモリリークを防止
- [x] イベントリスナーの重複登録を防止
- [x] setTimeoutのコールバックで適切にクリーンアップ

## デバッグ方法

### コンソールログ
各機能で以下のログを出力しています:

```javascript
console.log('String X (note) played');           // 弦がクリックされた
console.log('Chord changed to: X');              // コードが変更された
console.log('Practice started at:', time);       // 練習開始
console.log('Practice ended. Duration:', X);      // 練習終了
console.log('Practiced chords:', [...]));        // 練習したコード一覧
```

### Web Audio API デバッグ
```javascript
// AudioContextの状態を確認
console.log('AudioContext state:', audioContext.state);

// オシレーターの周波数を確認
console.log('Oscillator frequency:', oscillator.frequency.value);
```

## 実装ファイル

- `/static/js/guitar.js` - メインのJavaScriptファイル
- `/static/css/guitar.css` - スタイルシート（振動アニメーションを含む）
- `/apps/guitar/templates/guitar/guitar.html` - HTMLテンプレート

## 関連タスク

- タスク1.5: 仮想ギター基本画面実装（完了）
- タスク1.6: 仮想ギターJavaScript実装（現在のタスク）
- タスク1.7: 練習時間記録機能実装（次のタスク）
