/**
 * VirtuTune - Camera Gesture Recognition
 *
 * MediaPipe Handsを使用したカメラジェスチャー認識
 * ストロークジェスチャーを検出してギター音をトリガーする
 */

(function() {
    'use strict';

    /**
     * GestureRecognizer クラス
     *
     * MediaPipe Handsを使用して手のジェスチャーを認識する
     */
    class GestureRecognizer {
        constructor() {
            // MediaPipe Handsの初期化
            this.hands = new Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
                }
            });

            // Handsモデルの設定
            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.7,
                minTrackingConfidence: 0.7
            });

            // 結果コールバックの設定
            this.hands.onResults(this.onResults.bind(this));

            // 前回のランドマーク（移動検出用）
            this.prevLandmarks = null;

            // カメラインスタンス
            this.camera = null;

            // カメラアクティブフラグ
            this.isCameraActive = false;
        }

        /**
         * カメラを開始する
         * @param {HTMLVideoElement} videoElement - カメラ映像を表示するビデオ要素
         * @returns {Promise<void>}
         */
        async startCamera(videoElement) {
            try {
                // カメラアクセスのリクエスト
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        width: { ideal: 640 },
                        height: { ideal: 480 },
                        facingMode: 'user'
                    }
                });

                // ビデオ要素にストリームを設定
                videoElement.srcObject = stream;
                await videoElement.play();

                // MediaPipe Camera Utilsの初期化
                this.camera = new Camera(videoElement, {
                    onFrame: async () => {
                        if (this.isCameraActive) {
                            await this.hands.send({ image: videoElement });
                        }
                    },
                    width: 640,
                    height: 480
                });

                // カメラを開始
                await this.camera.start();
                this.isCameraActive = true;

                console.log('Camera started successfully');

            } catch (error) {
                console.error('Error starting camera:', error);
                throw error;
            }
        }

        /**
         * カメラを停止する
         */
        stopCamera() {
            if (this.camera) {
                this.camera.stop();
                this.camera = null;
            }

            this.isCameraActive = false;
            this.prevLandmarks = null;

            console.log('Camera stopped');
        }

        /**
         * MediaPipe Handsの結果を処理する
         * @param {Object} results - MediaPipe Handsの検出結果
         */
        onResults(results) {
            // プライバシー: 画像データは即座に破棄され、保存されない

            if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
                const landmarks = results.multiHandLandmarks[0];

                // ストロークジェスチャーの検出
                if (this.isStrumming(landmarks, this.prevLandmarks)) {
                    const velocity = this.strumVelocity(landmarks);
                    this.triggerNote(velocity);
                }

                // 現在のランドマークを保存
                this.prevLandmarks = landmarks;
            }
        }

        /**
         * ストロークジェスチャーかどうかを判定する
         * @param {Array} current - 現在の手のランドマーク
         * @param {Array} previous - 前回の手のランドマーク
         * @returns {boolean} ストロークと判定された場合はtrue
         */
        isStrumming(current, previous) {
            if (!previous) {
                return false;
            }

            // 手首（landmark 0）のY座標の変化を検知
            const currentY = current[0].y;
            const previousY = previous[0].y;
            const velocity = currentY - previousY;

            // 下方向への動きでストロークと判定（閾値は調整可能）
            const STRUM_THRESHOLD = 0.05;
            return velocity > STRUM_THRESHOLD;
        }

        /**
         * ストロークの速度を計算する
         * @param {Array} landmarks - 手のランドマーク
         * @returns {number} 速度（0-1の範囲）
         */
        strumVelocity(landmarks) {
            // 手首（landmark 0）と中指の先（landmark 12）の距離でVelocityを計算
            const wrist = landmarks[0];
            const middleTip = landmarks[12];

            const distance = Math.sqrt(
                Math.pow(wrist.x - middleTip.x, 2) +
                Math.pow(wrist.y - middleTip.y, 2)
            );

            // 0-1の範囲に正規化
            return Math.min(distance, 1.0);
        }

        /**
         * ギター音をトリガーする
         * @param {number} velocity - 音の速度
         */
        triggerNote(velocity) {
            // 音声再生イベント発火
            const event = new CustomEvent('strum', {
                detail: { velocity }
            });
            window.dispatchEvent(event);

            console.log('Strum triggered with velocity:', velocity);
        }

        /**
         * カメラがアクティブかどうかを確認する
         * @returns {boolean}
         */
        isActive() {
            return this.isCameraActive;
        }
    }

    // グローバルスコープに公開
    window.GestureRecognizer = GestureRecognizer;

    /**
     * カメラジェスチャー認識の初期化
     */
    document.addEventListener('DOMContentLoaded', function() {
        // ビデオ要素が存在する場合のみ初期化
        const videoElement = document.getElementById('camera-video');
        const enableCameraBtn = document.getElementById('enable-camera-btn');
        const disableCameraBtn = document.getElementById('disable-camera-btn');
        const cameraIndicator = document.getElementById('camera-indicator');

        if (videoElement && enableCameraBtn) {
            let gestureRecognizer = null;

            // カメラ有効化ボタン
            enableCameraBtn.addEventListener('click', async function() {
                try {
                    // GestureRecognizerのインスタンスを作成
                    gestureRecognizer = new GestureRecognizer();

                    // カメラを開始
                    await gestureRecognizer.startCamera(videoElement);

                    // UIの更新
                    enableCameraBtn.disabled = true;
                    disableCameraBtn.disabled = false;
                    cameraIndicator.classList.add('active');

                    // インジケーターテキストを更新
                    const indicatorText = cameraIndicator.querySelector('.indicator-text');
                    if (indicatorText) {
                        indicatorText.textContent = 'カメラ: オン';
                    }

                    console.log('Camera gesture recognition enabled');

                } catch (error) {
                    console.error('Failed to start camera:', error);
                    alert('カメラを開始できませんでした: ' + error.message);
                }
            });

            // カメラ無効化ボタン
            if (disableCameraBtn) {
                disableCameraBtn.addEventListener('click', function() {
                    if (gestureRecognizer) {
                        gestureRecognizer.stopCamera();
                        gestureRecognizer = null;
                    }

                    // UIの更新
                    enableCameraBtn.disabled = false;
                    disableCameraBtn.disabled = true;
                    cameraIndicator.classList.remove('active');

                    // インジケーターテキストを更新
                    const indicatorText = cameraIndicator.querySelector('.indicator-text');
                    if (indicatorText) {
                        indicatorText.textContent = 'カメラ: オフ';
                    }

                    // ビデオ要素をクリア
                    videoElement.srcObject = null;

                    console.log('Camera gesture recognition disabled');
                });
            }

            // ストロームイベントのリスナー
            window.addEventListener('strum', function(event) {
                const velocity = event.detail.velocity;

                // ゲームモードの場合はゲームにストロークを通知
                if (typeof rhythmGame !== 'undefined' && rhythmGame.isPlaying) {
                    // ゲーム側でハンドルされる
                    console.log('Game strum detected:', velocity);
                } else {
                    // フリーモードの場合は現在選択中のコードを再生
                    // TODO: コードに応じた音声再生ロジックを実装
                    console.log('Free mode strum detected:', velocity);
                }

                // 視覚的フィードバック
                const guitarNeck = document.querySelector('.guitar-neck');
                if (guitarNeck) {
                    guitarNeck.classList.add('strumming');
                    setTimeout(() => {
                        guitarNeck.classList.remove('strumming');
                    }, 200);
                }
            });
        }
    });

})();
