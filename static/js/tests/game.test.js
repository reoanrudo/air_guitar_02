/**
 * テスト: リズムゲーム (game.js)
 *
 * リズムゲームの機能をテストする
 */

describe('RhythmGame', () => {
    let game;
    let mockCanvas;
    let mockContext;

    beforeEach(() => {
        // Canvasのモックを作成
        mockCanvas = document.createElement('canvas');
        mockContext = {
            fillStyle: '',
            fillRect: jasmine.createSpy('fillRect'),
            fillText: jasmine.createSpy('fillText'),
            clearRect: jasmine.createSpy('clearRect'),
            beginPath: jasmine.createSpy('beginPath'),
            closePath: jasmine.createSpy('closePath'),
            arc: jasmine.createSpy('arc'),
            fill: jasmine.createSpy('fill')
        };

        mockCanvas.getContext = () => mockContext;

        // ゲームインスタンスを作成
        game = new RhythmGame(mockCanvas);

        // requestAnimationFrameのモック
        spyOn(window, 'requestAnimationFrame').and.callFake(cb => {
            setTimeout(cb, 16);
        });
    });

    afterEach(() => {
        if (game.isPlaying) {
            game.stop();
        }
    });

    describe('初期化', () => {
        it('ゲームが正しく初期化されること', () => {
            expect(game).toBeDefined();
            expect(game.isPlaying).toBe(false);
            expect(game.score).toBe(0);
            expect(game.combo).toBe(0);
            expect(game.notes).toEqual([]);
        });

        it('タイミング判定基準が正しく設定されること', () => {
            expect(game.timingWindows.perfect).toBe(50);
            expect(game.timingWindows.great).toBe(100);
            expect(game.timingWindows.good).toBe(150);
        });
    });

    describe('start()', () => {
        const mockSongData = {
            id: 1,
            name: 'Test Song',
            tempo: 120,
            notes: [
                { timing: 0.0, note: 'C', duration: 1.0 },
                { timing: 1.0, note: 'G', duration: 1.0 },
                { timing: 2.0, note: 'Am', duration: 1.0 }
            ]
        };

        it('楽曲データでゲームが開始されること', () => {
            game.start(mockSongData);

            expect(game.isPlaying).toBe(true);
            expect(game.currentSong).toEqual(mockSongData);
            expect(game.notes.length).toBe(3);
            expect(game.score).toBe(0);
            expect(game.combo).toBe(0);
        });

        it('開始時に統計がリセットされること', () => {
            game.score = 1000;
            game.combo = 10;
            game.stats.perfect = 5;

            game.start(mockSongData);

            expect(game.score).toBe(0);
            expect(game.combo).toBe(0);
            expect(game.stats.perfect).toBe(0);
        });
    });

    describe('stop()', () => {
        it('ゲームが正しく停止されること', () => {
            const mockSongData = {
                id: 1,
                name: 'Test Song',
                tempo: 120,
                notes: []
            };

            game.start(mockSongData);
            game.stop();

            expect(game.isPlaying).toBe(false);
        });
    });

    describe('checkHit()', () => {
        beforeEach(() => {
            game.start({
                id: 1,
                name: 'Test Song',
                tempo: 120,
                notes: [
                    { timing: 0.0, note: 'C', duration: 1.0 },
                    { timing: 1.0, note: 'G', duration: 1.0 },
                    { timing: 2.0, note: 'Am', duration: 1.0 }
                ]
            });
            game.startTime = Date.now();
        });

        it('Perfect判定が正しく動作すること', () => {
            game.startTime = Date.now() - 30; // 30ms経過

            const result = game.checkHit('C', Date.now());
            expect(result.judgement).toBe('PERFECT');
            expect(result.score).toBe(100);
            expect(game.combo).toBe(1);
        });

        it('Great判定が正しく動作すること', () => {
            game.startTime = Date.now() - 80; // 80ms経過

            const result = game.checkHit('C', Date.now());
            expect(result.judgement).toBe('GREAT');
            expect(result.score).toBe(80);
            expect(game.combo).toBe(1);
        });

        it('Good判定が正しく動作すること', () => {
            game.startTime = Date.now() - 120; // 120ms経過

            const result = game.checkHit('C', Date.now());
            expect(result.judgement).toBe('GOOD');
            expect(result.score).toBe(60);
            expect(game.combo).toBe(1);
        });

        it('Miss判定が正しく動作すること', () => {
            game.startTime = Date.now() - 200; // 200ms経過

            const result = game.checkHit('C', Date.now());
            expect(result.judgement).toBe('MISS');
            expect(result.score).toBe(0);
            expect(game.combo).toBe(0);
        });

        it('コンボが正しくカウントされること', () => {
            game.startTime = Date.now() - 30;

            game.checkHit('C', Date.now());
            expect(game.combo).toBe(1);

            game.startTime = Date.now() - 1030; // 1秒後
            game.checkHit('G', Date.now());
            expect(game.combo).toBe(2);
        });

        it('Missでコンボがリセットされること', () => {
            game.startTime = Date.now() - 30;
            game.checkHit('C', Date.now());
            expect(game.combo).toBe(1);

            game.startTime = Date.now() - 1030; // 1秒後
            game.checkHit('Wrong', Date.now()); // 間違ったノート
            expect(game.combo).toBe(0);
        });
    });

    describe('calculateScore()', () => {
        it('スコアが正しく計算されること', () => {
            game.stats = {
                perfect: 10,
                great: 5,
                good: 3,
                miss: 2
            };

            const score = game.calculateScore();
            // Perfect: 10 * 100 = 1000
            // Great: 5 * 80 = 400
            // Good: 3 * 60 = 180
            // 合計: 1580
            expect(score).toBe(1580);
        });
    });

    describe('calculateAccuracy()', () => {
        it('精度が正しく計算されること', () => {
            game.stats = {
                perfect: 10,
                great: 5,
                good: 3,
                miss: 2
            };

            const accuracy = game.calculateAccuracy();
            // (10 * 1.0 + 5 * 0.8 + 3 * 0.6) / 20 = 0.79
            expect(accuracy).toBeCloseTo(0.79, 2);
        });

        it('全Perfectで100%になること', () => {
            game.stats = {
                perfect: 10,
                great: 0,
                good: 0,
                miss: 0
            };

            const accuracy = game.calculateAccuracy();
            expect(accuracy).toBe(1.0);
        });

        it('全Missで0%になること', () => {
            game.stats = {
                perfect: 0,
                great: 0,
                good: 0,
                miss: 10
            };

            const accuracy = game.calculateAccuracy();
            expect(accuracy).toBe(0.0);
        });
    });

    describe('updateNotes()', () => {
        it('ノートが正しく更新されること', () => {
            game.start({
                id: 1,
                name: 'Test Song',
                tempo: 120,
                notes: [
                    { timing: 0.0, note: 'C', duration: 1.0, x: 1000 }
                ]
            });

            game.updateNotes(0.016); // 16ms経過

            // ノートが左に移動していることを確認
            expect(game.notes[0].x).toBeLessThan(1000);
        });

        it('画面外のノートが削除されること', () => {
            game.start({
                id: 1,
                name: 'Test Song',
                tempo: 120,
                notes: [
                    { timing: 0.0, note: 'C', duration: 1.0, x: -100 }
                ]
            });

            game.updateNotes(0.016);

            expect(game.notes.length).toBe(0);
        });
    });

    describe('getStats()', () => {
        it('統計情報が正しく取得されること', () => {
            game.stats = {
                perfect: 10,
                great: 5,
                good: 3,
                miss: 2
            };
            game.score = 1580;
            game.combo = 8;

            const stats = game.getStats();

            expect(stats.score).toBe(1580);
            expect(stats.maxCombo).toBe(8);
            expect(stats.perfectCount).toBe(10);
            expect(stats.greatCount).toBe(5);
            expect(stats.goodCount).toBe(3);
            expect(stats.missCount).toBe(2);
            expect(stats.accuracy).toBeDefined();
        });
    });
});
