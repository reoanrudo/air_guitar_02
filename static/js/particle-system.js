/**
 * VirtuTune - Particle System
 *
 * Air Guitar Pro からの移植
 * パーティクルエフェクトシステム
 */

(function() {
    'use strict';

    /**
     * ParticleSystemクラス
     * ヒット/ストローク時のパーティクルエフェクト
     */
    class ParticleSystem {
        constructor() {
            this.particles = [];
            this.maxParticles = 100;
            this.canvas = null;
            this.ctx = null;
            this.animationFrameId = null;
        }

        /**
         * Canvasを初期化
         * @param {HTMLElement} canvasElement - Canvas要素
         */
        initializeCanvas(canvasElement) {
            this.canvas = canvasElement;
            this.ctx = canvasElement.getContext('2d');

            // Canvasサイズを設定
            this.canvas.width = this.canvas.offsetWidth || window.innerWidth;
            this.canvas.height = this.canvas.offsetHeight || window.innerHeight;

            // ウィンドウサイズ変更イベント
            window.addEventListener('resize', () => {
                this.canvas.width = this.canvas.offsetWidth || window.innerWidth;
                this.canvas.height = this.canvas.offsetHeight || window.innerHeight;
            });
        }

        /**
         * パーティクルを生成
         * @param {number} x - X座標
         * @param {number} y - Y座標
         * @param {number} count - 生成数
         * @param {string} color - 色（HEXまたはRGB）
         * @param {number} velocityScale - 速度スケール係数
         */
        spawn(x, y, count, color, velocityScale = 1.0) {
            // 最大数制限を超えないようにする
            if (this.particles.length >= this.maxParticles) {
                return;
            }

            for (let i = 0; i < count; i++) {
                // ランダムな速度（球状に広がる）
                const angle = Math.random() * Math.PI * 2;
                const speed = Math.random() * 50 * velocityScale;

                this.particles.push({
                    x: x,
                    y: y,
                    vx: Math.cos(angle) * speed,
                    vy: Math.sin(angle) * speed,
                    life: 1.0,
                    decay: 0.02 + Math.random() * 0.02,
                    color: color,
                    size: 3 + Math.random() * 5
                });
            }
        }

        /**
         * ヒット時のパーティクル（多め、黄色系）
         * @param {number} x - X座標
         * @param {number} y - Y座標
         */
        spawnHitParticles(x, y) {
            const colors = ['#ffd700', '#ffed4e', '#ffffff'];
            const color = colors[Math.floor(Math.random() * colors.length)];
            this.spawn(x, y, 25, color, 1.2);
        }

        /**
         * ストローク時のパーティクル（少なめ、オレンジ系）
         * @param {number} x - X座標
         * @param {number} y - Y座標
         */
        spawnStrumParticles(x, y) {
            const colors = ['#f97316', '#fbbf24', '#ff6b6b'];
            const color = colors[Math.floor(Math.random() * colors.length)];
            this.spawn(x, y, 15, color, 0.8);
        }

        /**
         * ストローク時のパーティクル（少なめ、オレンジ系）
         * @param {number} x - X座標
         * @param {number} y - Y座標
         */
        spawnStrumParticles(x, y) {
            const colors = ['#f97316', '#fbbf24', '#ff6b6b'];
            const color = colors[Math.floor(Math.random() * colors.length)];
            this.spawn(x, y, 15, color, 0.8);
        }

        /**
         * コンボマイルストーン時のパーティクル
         * @param {number} x - X座標
         * @param {number} y - Y座標
         * @param {number} combo - コンボ数
         */
        spawnComboParticles(x, y, combo) {
            const color = '#a855f7';
            const count = Math.min(combo, 50);
            this.spawn(x, y, count, color, 1.5);
        }

        /**
         * 物理演算を更新
         */
        update() {
            for (let i = this.particles.length - 1; i >= 0; i--) {
                const p = this.particles[i];

                // 位置を更新
                p.x += p.vx;
                p.y += p.vy;

                // 重力を適用（微々に下向き）
                p.vy += 0.5;

                // 減衰を適用
                p.life -= p.decay;

                // 期限切れのパーティクルを削除
                if (p.life <= 0) {
                    this.particles.splice(i, 1);
                }
            }
        }

        /**
         * Canvasにパーティクルを描画
         */
        render() {
            if (!this.ctx) return;

            // Canvasをクリア
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            // 各パーティクルを描画
            this.particles.forEach(p => {
                this.ctx.save();
                this.ctx.globalAlpha = p.life;
                this.ctx.fillStyle = p.color;
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.restore();
            });
        }

        /**
         * アニメーションループを開始
         */
        start() {
            if (this.animationFrameId) return;

            const loop = () => {
                this.update();
                this.render();
                this.animationFrameId = requestAnimationFrame(loop);
            };

            loop();
        }

        /**
         * アニメーションループを停止
         */
        stop() {
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
                this.animationFrameId = null;
            }
        }

        /**
         * 全パーティクルをクリア
         */
        clear() {
            this.particles = [];
        }
    }

    // グローバルスコープに公開
    window.ParticleSysytem = ParticleSystem;

})();
