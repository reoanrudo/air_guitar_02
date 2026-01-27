# 仮想ギターJavaScript - クイックリファレンス

## ファイル構成

```
/static/js/guitar.js          - メイン実装（7.8KB）
/static/css/guitar.css        - スタイルとアニメーション
/static/sounds/strings/       - 音声ファイル用ディレクトリ（現在使用せず）
```

## 主要な関数

### 音声再生
```javascript
playGuitarSound(stringNumber, note)
```
- **引数**: `stringNumber` (1-6), `note` (音符名)
- **機能**: Web Audio APIでギター音を合成
- **戻り値**: なし

### アニメーション
```javascript
animateString(stringElement)
```
- **引数**: `stringElement` (HTMLElement)
- **機能**: 弦の振動アニメーションを開始
- **戻り値**: なし

### コード管理
```javascript
changeChord(chordName)
```
- **引数**: `chordName` (コード名)
- **機能**: 現在のコードを変更してUIを更新
- **戻り値**: なし

### タイマー制御
```javascript
startPractice()
stopPractice()
updateTimer()
```
- **機能**: 練習セッションの開始/終了/タイマー更新

## グローバル変数

```javascript
let currentChord = null;           // 現在選択されているコード
let practiceStartTime = null;      // 練習開始時刻
let timerInterval = null;          // タイマー間隔ID
let practicedChords = new Set();   // 練習したコードの集合
```

## イベントリスナー

### ページ読み込み時
```javascript
DOMContentLoaded
  ├── initializeGuitar()
  ├── initializeChordSelector()
  └── initializePracticeControls()
```

### ユーザー操作
```javascript
.string クリック          → playString() + animateString()
.chord-btn クリック       → changeChord()
#start-practice クリック  → startPractice()
#stop-practice クリック   → stopPractice()
```

## Web Audio API設定

### 周波数マッピング
```javascript
{
  '6': 82.41,   // E2
  '5': 110.00,  // A2
  '4': 146.83,  // D2
  '3': 196.00,  // G1
  '2': 246.94,  // B1
  '1': 329.63   // e1
}
```

### オシレーター設定
```javascript
oscillator.type = 'triangle'           // 三角波
oscillator.frequency = <各弦の周波数>
gainNode.gain.attack = 0.01s           // アタック
gainNode.gain.decay = 1.0s             // ディケイ
```

## CSSアニメーション

### 振動アニメーション
```css
.string.vibrating {
  animation: vibrate 0.1s linear 3;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
}
```

### アクティブ状態
```css
.chord-btn.active {
  background: #667eea;
  color: white;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.5);
}
```

## デバッグ

### コンソールログ出力
```javascript
// 弦がクリックされた
console.log(`String ${stringNumber} (${note}) played`);

// コードが変更された
console.log(`Chord changed to: ${chordName}`);

// 練習開始
console.log('Practice started at:', practiceStartTime);

// 練習終了
console.log('Practice ended. Duration:', duration, 'seconds');
console.log('Practiced chords:', Array.from(practicedChords));
```

### ブラウザ開発者ツールで確認
1. F12 または Cmd+Option+I で開発者ツールを開く
2. Consoleタブでログを確認
3. Elementsタブでクラスの変化を確認
4. Networkタブでリクエストを確認（将来API実装時）

## 既知の問題と解決策

### 音が鳴らない
- **原因**: ブラウザの自動再生ポリシー
- **解決**: ユーザー操作（クリック）後に初めて鳴る

### アニメーションが見えない
- **原因**: CSSが読み込まれていない
- **解決**: `guitar.css`が正しくリンクされているか確認

### メモリリーク
- **対策**: AudioContextを適切にクローズ
- **確認**: 長時間使用してメモリ使用量を監視

## 次のステップへの接続

### タスク1.7（練習時間記録）で実装
```javascript
// TODO: 練習開始APIを呼び出し
// TODO: 練習終了APIを呼び出し
// TODO: 練習記録を保存
```

### APIエンドポイント（予定）
```
POST /api/guitar/practice/start/  - 練習開始
POST /api/guitar/practice/end/    - 練習終了
GET  /api/guitar/practice/history/ - 練習履歴
```

## テストコマンド

### 構文チェック
```bash
node --check static/js/guitar.js
```

### Djangoサーバー起動
```bash
python manage.py runserver
```

### アクセスURL
```
http://localhost:8000/guitar/
```

## パフォーマンスチェックリスト

- [x] 不要なイベントリスナーを削除
- [x] AudioContextを適切にクローズ
- [x] setTimeoutのクリーンアップ
- [x] DOM操作の最小化
- [x] グローバル名前空間の汚染を回避（IIFE使用）

---

**最終更新**: 2026-01-27
**実装完了**: Task 1.6
**次のタスク**: Task 1.7（練習時間記録機能）
