/**
 * Game Integration Tests
 *
 * WebSocket/Camera連携ゲームモードの統合テスト
 */

describe('Game Integration', () => {
    let game;
    let mockCanvas;
    let mockContext;

    beforeEach(() => {
        // モックキャンバスの設定
        mockCanvas = document.createElement('canvas');
        mockCanvas.width = 800;
        mockCanvas.height = 600;
        mockContext = {
            clearRect: jest.fn(),
            strokeStyle: null,
            lineWidth: null,
            fillStyle: null,
            font: null,
            textAlign: null,
            textBaseline: null,
            beginPath: jest.fn(),
            moveTo: jest.fn(),
            lineTo: jest.fn(),
            stroke: jest.fn(),
            fill: jest.fn(),
            fillRect: jest.fn(),
            arc: jest.fn(),
            fillText: jest.fn(),
            createRadialGradient: jest.fn().mockReturnValue({
                addColorStop: jest.fn()
            })
        };
        mockCanvas.getContext = jest.fn().mockReturnValue(mockContext);

        // ゲームインスタンスの作成
        game = new RhythmGame(mockCanvas);
    });

    afterEach(() => {
        if (game) {
            game.stop();
        }
    });

    describe('WebSocket Integration', () => {
        test('should setup WebSocket connection with session ID', () => {
            const sessionId = 'test-session-123';
            game.setupWebSocket(sessionId);

            expect(game.sessionId).toBe(sessionId);
            expect(game.ws).toBeDefined();
        });

        test('should send game mode on WebSocket connection', () => {
            const sessionId = 'test-session-123';
            const mockWs = {
                send: jest.fn(),
                close: jest.fn()
            };

            game.setupWebSocket(sessionId);
            game.ws = mockWs;

            // 接続成功時のシミュレーション
            game.ws.onopen();

            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining('"game_mode"')
            );
        });

        test('should handle chord change messages from WebSocket', () => {
            const mockData = {
                type: 'chord_change',
                data: { chord: 'C' }
            };

            game.handleWebSocketMessage(mockData);

            expect(game.currentChord).toBe('C');
        });

        test('should handle game update messages from WebSocket', () => {
            const mockData = {
                type: 'game_update',
                data: {
                    score: 1000,
                    combo: 10
                }
            };

            game.handleWebSocketMessage(mockData);

            expect(game.score).toBe(1000);
            expect(game.combo).toBe(10);
        });

        test('should send game state updates via WebSocket', () => {
            const sessionId = 'test-session-123';
            const mockWs = {
                readyState: WebSocket.OPEN,
                send: jest.fn()
            };

            game.setupWebSocket(sessionId);
            game.ws = mockWs;
            game.score = 500;
            game.combo = 5;

            game.sendGameState();

            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining('"score":500')
            );
            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining('"combo":5')
            );
        });

        test('should sync score from mobile device', () => {
            game.score = 1000;
            game.syncScore(1500);

            expect(game.score).toBe(1500);
        });

        test('should sync combo from mobile device', () => {
            game.combo = 10;
            game.syncCombo(20);

            expect(game.combo).toBe(20);
        });
    });

    describe('Camera Gesture Integration', () => {
        test('should enable camera for game mode', () => {
            expect(game.cameraEnabled).toBe(false);

            game.enableCamera();

            expect(game.cameraEnabled).toBe(true);
        });

        test('should disable camera', () => {
            game.enableCamera();
            game.disableCamera();

            expect(game.cameraEnabled).toBe(false);
        });

        test('should handle strum gesture when camera is enabled', () => {
            const mockSongData = {
                id: 1,
                notes: [
                    { timing: 1.0, note: 'C', duration: 0.5 }
                ]
            };

            game.enableCamera();
            game.currentChord = 'C';
            game.start(mockSongData);

            // ストロークをシミュレート
            const strumEvent = new CustomEvent('strum', {
                detail: { velocity: 0.8 }
            });
            window.dispatchEvent(strumEvent);

            // ヒット判定が行われることを確認
            expect(game.stats.miss + game.stats.perfect + game.stats.great + game.stats.good).toBeGreaterThan(0);
        });

        test('should not handle strum when camera is disabled', () => {
            const mockSongData = {
                id: 1,
                notes: [
                    { timing: 1.0, note: 'C', duration: 0.5 }
                ]
            };

            game.currentChord = 'C';
            game.start(mockSongData);

            const initialHits = game.stats.perfect + game.stats.great + game.stats.good;

            // カメラが無効な状態でストローク
            const strumEvent = new CustomEvent('strum', {
                detail: { velocity: 0.8 }
            });
            window.dispatchEvent(strumEvent);

            // ヒット数が変化しないことを確認
            expect(game.stats.perfect + game.stats.great + game.stats.good).toBe(initialHits);
        });
    });

    describe('Game Session Management', () => {
        test('should start game with practice session tracking', () => {
            const mockSongData = {
                id: 1,
                name: 'Test Song',
                notes: []
            };

            game.start(mockSongData);

            expect(game.isPlaying).toBe(true);
            expect(game.currentSong).toBe(mockSongData);
            expect(game.startTime).toBeGreaterThan(0);
        });

        test('should stop game and save results', () => {
            const mockSongData = {
                id: 1,
                name: 'Test Song',
                notes: []
            };

            game.start(mockSongData);
            game.stop();

            expect(game.isPlaying).toBe(false);
            expect(game.isPaused).toBe(false);
        });

        test('should handle practice start message from mobile', () => {
            const mockSongData = {
                id: 1,
                name: 'Test Song',
                notes: []
            };

            game.currentSong = mockSongData;

            const mockData = {
                type: 'practice_update',
                data: { status: 'started' }
            };

            game.handleWebSocketMessage(mockData);

            expect(game.isPlaying).toBe(true);
        });

        test('should handle practice end message from mobile', () => {
            const mockSongData = {
                id: 1,
                name: 'Test Song',
                notes: []
            };

            game.start(mockSongData);

            const mockData = {
                type: 'practice_update',
                data: { status: 'ended' }
            };

            game.handleWebSocketMessage(mockData);

            expect(game.isPlaying).toBe(false);
        });

        test('should handle game pause toggle from mobile', () => {
            const mockSongData = {
                id: 1,
                name: 'Test Song',
                notes: []
            };

            game.start(mockSongData);
            expect(game.isPaused).toBe(false);

            const mockData = {
                type: 'game_pause'
            };

            game.handleWebSocketMessage(mockData);

            expect(game.isPaused).toBe(true);
        });
    });

    describe('Real-time Score Sync', () => {
        test('should send judgement result via WebSocket', () => {
            const sessionId = 'test-session-123';
            const mockWs = {
                readyState: WebSocket.OPEN,
                send: jest.fn()
            };

            game.setupWebSocket(sessionId);
            game.ws = mockWs;

            game.sendJudgement('PERFECT', 100);

            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining('"judgement":"PERFECT"')
            );
            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining('"score":100')
            );
        });

        test('should update UI and sync on score change', () => {
            const sessionId = 'test-session-123';
            const mockWs = {
                readyState: WebSocket.OPEN,
                send: jest.fn()
            };

            game.setupWebSocket(sessionId);
            game.ws = mockWs;

            game.score = 100;
            game.combo = 5;
            game.updateUI();

            expect(mockWs.send).toHaveBeenCalled();
        });

        test('should sync combo across devices', () => {
            const sessionId = 'test-session-123';
            const mockWs = {
                readyState: WebSocket.OPEN,
                send: jest.fn()
            };

            game.setupWebSocket(sessionId);
            game.ws = mockWs;
            game.combo = 10;

            game.sendGameState();

            expect(mockWs.send).toHaveBeenCalledWith(
                expect.stringContaining('"combo":10')
            );
        });
    });

    describe('Device Pairing State', () => {
        test('should show current chord when received from mobile', () => {
            const mockElement = document.createElement('div');
            mockElement.id = 'current-chord-display';
            document.body.appendChild(mockElement);

            game.showCurrentChord('G');

            expect(mockElement.textContent).toBe('G');
            expect(mockElement.classList.contains('highlight')).toBe(true);

            document.body.removeChild(mockElement);
        });

        test('should cleanup WebSocket on game stop', () => {
            const sessionId = 'test-session-123';
            const mockWs = {
                close: jest.fn()
            };

            game.setupWebSocket(sessionId);
            game.ws = mockWs;
            game.stop();

            expect(mockWs.close).toHaveBeenCalled();
            expect(game.ws).toBe(null);
        });
    });
});
