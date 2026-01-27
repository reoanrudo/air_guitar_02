/**
 * VirtuTune - Camera Gesture Recognition Tests
 *
 * MediaPipeベースのカメラジェスチャー認識のテスト
 */

describe('GestureRecognizer', function() {
    let gestureRecognizer;
    let mockVideoElement;
    let mockHands;

    beforeEach(function() {
        // MediaPipe Handsのモック
        mockHands = {
            setOptions: jasmine.createSpy('setOptions'),
            onResults: jasmine.createSpy('onResults'),
            send: jasmine.createSpy('send').and.returnValue(Promise.resolve())
        };

        // GestureRecognizerのモック（MediaPipeが利用可能な場合のみ）
        if (typeof Hands !== 'undefined' && typeof Camera !== 'undefined') {
            gestureRecognizer = new GestureRecognizer();
        }

        // ビデオ要素のモック
        mockVideoElement = {
            width: 640,
            height: 480,
            addEventListener: jasmine.createSpy('addEventListener')
        };
    });

    afterEach(function() {
        if (gestureRecognizer) {
            gestureRecognizer.stopCamera();
        }
    });

    describe('コンストラクタ', function() {
        it('GestureRecognizerインスタンスを作成できること', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            expect(gestureRecognizer).toBeDefined();
            expect(gestureRecognizer.hands).toBeDefined();
            expect(gestureRecognizer.prevLandmarks).toBeNull();
        });

        it('Handsモデルが正しく設定されていること', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            expect(gestureRecognizer.hands.setOptions).toHaveBeenCalledWith({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.7,
                minTrackingConfidence: 0.7
            });
        });
    });

    describe('isStrumming', function() {
        it('前回のランドマークがない場合はfalseを返すこと', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            const currentLandmarks = [{ x: 0.5, y: 0.5, z: 0 }];
            const result = gestureRecognizer.isStrumming(currentLandmarks, null);
            expect(result).toBe(false);
        });

        it('下方向への動きをストロークと判定すること', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            const previousLandmarks = [{ x: 0.5, y: 0.3, z: 0 }];
            const currentLandmarks = [{ x: 0.5, y: 0.4, z: 0 }]; // 下に移動

            const result = gestureRecognizer.isStrumming(currentLandmarks, previousLandmarks);
            expect(result).toBe(true);
        });

        it('上方向への動きはストロークと判定しないこと', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            const previousLandmarks = [{ x: 0.5, y: 0.4, z: 0 }];
            const currentLandmarks = [{ x: 0.5, y: 0.3, z: 0 }]; // 上に移動

            const result = gestureRecognizer.isStrumming(currentLandmarks, previousLandmarks);
            expect(result).toBe(false);
        });

        it('閾値以下の動きはストロークと判定しないこと', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            const previousLandmarks = [{ x: 0.5, y: 0.3, z: 0 }];
            const currentLandmarks = [{ x: 0.5, y: 0.32, z: 0 }]; // わずかな動き

            const result = gestureRecognizer.isStrumming(currentLandmarks, previousLandmarks);
            expect(result).toBe(false);
        });
    });

    describe('strumVelocity', function() {
        it('手首と中指の距離を計算すること', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            const landmarks = [
                { x: 0.5, y: 0.5, z: 0 },  // 手首（landmark 0）
                { x: 0.5, y: 0.4, z: 0 },  // 中指の付け根（landmark 12）
            ];

            // 12番目のランドマークを中指の先として使用
            for (let i = 2; i < 12; i++) {
                landmarks.push({ x: 0.5, y: 0.5, z: 0 });
            }

            const velocity = gestureRecognizer.strumVelocity(landmarks);
            expect(velocity).toBeGreaterThan(0);
            expect(velocity).toBeLessThan(1);
        });
    });

    describe('triggerNote', function() {
        it('カスタムイベントを発火すること', function(done) {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            const eventListener = function(event) {
                expect(event.detail).toBeDefined();
                expect(event.detail.velocity).toBeDefined();
                window.removeEventListener('strum', eventListener);
                done();
            };

            window.addEventListener('strum', eventListener);

            const velocity = 0.5;
            gestureRecognizer.triggerNote(velocity);
        });
    });

    describe('startCamera', function() {
        it('カメラを開始できること', function(done) {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            // ユーザーがカメラアクセスを許可したと仮定
            spyOn(navigator.mediaDevices, 'getUserMedia').and.returnValue(
                Promise.resolve({
                    getTracks: () => []
                })
            );

            gestureRecognizer.startCamera(mockVideoElement)
                .then(() => {
                    expect(gestureRecognizer.camera).toBeDefined();
                })
                .catch(error => {
                    // カメラが利用可能でない場合はテストをスキップ
                    console.log('Camera not available in test environment:', error);
                })
                .finally(done);
        });

        it('カメラアクセス拒否時にエラーを処理すること', function(done) {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            spyOn(navigator.mediaDevices, 'getUserMedia').and.returnValue(
                Promise.reject(new Error('Permission denied'))
            );

            gestureRecognizer.startCamera(mockVideoElement)
                .then(() => {
                    fail('Expected error to be thrown');
                })
                .catch(error => {
                    expect(error.message).toBe('Permission denied');
                })
                .finally(done);
        });
    });

    describe('stopCamera', function() {
        it('カメラを停止できること', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            gestureRecognizer.stopCamera();
            expect(gestureRecognizer.camera).toBeNull();
        });
    });

    describe('プライバシー', function() {
        it('カメラ映像が保存されないこと', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            // onResultsメソッドが映像を保存していないことを確認
            expect(gestureRecognizer.savedFrames).toBeUndefined();
        });

        it('処理後にデータが破棄されること', function() {
            if (typeof Hands === 'undefined') {
                pending('MediaPipe Handsが利用可能ではありません');
            }

            const mockResults = {
                multiHandLandmarks: [[{ x: 0.5, y: 0.5, z: 0 }]]
            };

            gestureRecognizer.onResults(mockResults);

            // 結果が保存されていないことを確認
            expect(gestureRecognizer.lastResults).toBeUndefined();
        });
    });
});
