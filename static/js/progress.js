/**
 * Progress Page JavaScript for VirtuTune
 *
 * 進捗表示ページのインタラクティブ機能
 * - Chart.jsによる練習グラフの描画
 * - 統計データの表示更新
 * - 7日/30日グラフ切り替え
 */

// グラフインスタンスを保持
let practiceChart = null;
let currentPeriod = 7; // デフォルトは7日間

// ページ読み込み時に実行
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    initializeChartPeriodToggle();
    initializeProgressBar();
    initializeGoalAnimation();
    initializeEncouragementMessages();
});

/**
 * プログレスバーのアニメーション初期化
 */
function initializeProgressBar() {
    const progressBarFill = document.getElementById('progress-bar-fill');
    const progressPercentage = document.getElementById('progress-percentage');

    if (progressBarFill && progressPercentage) {
        // パーセンテージを取得
        const targetWidth = progressBarFill.style.width;
        const targetPercentage = parseInt(targetWidth) || 0;

        // アニメーション開始
        setTimeout(() => {
            progressBarFill.style.width = targetWidth;

            // パーセンテージをカウントアップ
            animateCounter(progressPercentage, 0, targetPercentage, 1000);
        }, 100);
    }
}

/**
 * カウンターのアニメーション
 */
function animateCounter(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16); // 60fps
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.round(current) + '%';
    }, 16);
}

/**
 * 目標達成時のアニメーション初期化
 */
function initializeGoalAnimation() {
    const goalSection = document.getElementById('goal-section');
    const goalCard = goalSection?.querySelector('.goal-card');

    if (goalCard && goalCard.classList.contains('goal-achieved')) {
        // 達成時のエフェクト
        createConfetti();
    }
}

/**
 * コンフェティエフェクト
 */
function createConfetti() {
    const colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe'];

    for (let i = 0; i < 50; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.cssText = `
                position: fixed;
                width: 10px;
                height: 10px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                left: ${Math.random() * 100}vw;
                top: -10px;
                border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
                animation: confetti-fall ${2 + Math.random() * 2}s linear forwards;
                z-index: 1000;
                pointer-events: none;
            `;

            document.body.appendChild(confetti);

            // アニメーション後に要素を削除
            setTimeout(() => {
                confetti.remove();
            }, 4000);
        }, i * 30);
    }

    // コンフェティアニメーション用のCSSを追加
    if (!document.getElementById('confetti-styles')) {
        const style = document.createElement('style');
        style.id = 'confetti-styles';
        style.textContent = `
            @keyframes confetti-fall {
                0% {
                    transform: translateY(0) rotate(0deg);
                    opacity: 1;
                }
                100% {
                    transform: translateY(100vh) rotate(720deg);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

/**
 * 練習グラフを初期化（Chart.js）
 */
function initializeChart() {
    const canvas = document.getElementById('practiceChart');
    if (!canvas) {
        console.warn('Chart canvas not found');
        return;
    }

    // データが空の場合はグラフを作成しない
    if (!dailyStats || dailyStats.length === 0) {
        console.info('No daily stats data available');
        return;
    }

    // グラフを作成
    createChart(dailyStats, 7);
}

/**
 * グラフを作成
 */
function createChart(statsData, period) {
    const canvas = document.getElementById('practiceChart');
    if (!canvas) return;

    // 既存のグラフを破棄
    if (practiceChart) {
        practiceChart.destroy();
    }

    // グラフデータの準備
    const labels = statsData.map(stat => {
        const date = new Date(stat.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });

    const data = statsData.map(stat => stat.minutes);

    // グラフの設定
    const ctx = canvas.getContext('2d');

    // VirtuTuneカラー theme
    const primaryColor = 'rgb(102, 126, 234)';
    const secondaryColor = 'rgb(118, 75, 162)';
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(102, 126, 234, 0.5)');
    gradient.addColorStop(1, 'rgba(118, 75, 162, 0.1)');

    practiceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '練習時間（分）',
                data: data,
                borderColor: primaryColor,
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: primaryColor,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: period === 30 ? 3 : 5,
                pointHoverRadius: period === 30 ? 5 : 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14,
                            family: "'Noto Sans JP', sans-serif"
                        },
                        color: '#2d3748'
                    }
                },
                title: {
                    display: false,
                    text: period === 7 ? '過去7日間の練習記録' : '過去30日間の練習記録'
                },
                tooltip: {
                    backgroundColor: 'rgba(45, 55, 72, 0.9)',
                    titleFont: {
                        size: 14,
                        family: "'Noto Sans JP', sans-serif"
                    },
                    bodyFont: {
                        size: 13,
                        family: "'Noto Sans JP', sans-serif"
                    },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return `練習時間: ${context.parsed.y}分`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: '練習時間（分）',
                        font: {
                            size: 12,
                            family: "'Noto Sans JP', sans-serif"
                        },
                        color: '#4a5568'
                    },
                    ticks: {
                        stepSize: period === 30 ? 10 : 5,
                        font: {
                            size: 11,
                            family: "'Noto Sans JP', sans-serif"
                        },
                        color: '#718096'
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '日付',
                        font: {
                            size: 12,
                            family: "'Noto Sans JP', sans-serif"
                        },
                        color: '#4a5568'
                    },
                    ticks: {
                        font: {
                            size: 11,
                            family: "'Noto Sans JP', sans-serif"
                        },
                        color: '#718096',
                        maxRotation: period === 30 ? 45 : 0,
                        minRotation: period === 30 ? 45 : 0
                    },
                    grid: {
                        display: false
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });

    console.info(`Practice chart initialized successfully (${period}-day period)`);
}

/**
 * グラフ期間切り替えボタンを初期化
 */
function initializeChartPeriodToggle() {
    const periodButtons = document.querySelectorAll('.period-btn');

    periodButtons.forEach(button => {
        button.addEventListener('click', function() {
            const period = parseInt(this.getAttribute('data-period'));

            // 現在の期間と同じ場合は何もしない
            if (period === currentPeriod) {
                return;
            }

            // ボタンのアクティブ状態を更新
            periodButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // 期間を更新
            currentPeriod = period;

            // グラフを更新
            updateChartPeriod(period);
        });
    });
}

/**
 * グラフの期間を更新
 */
function updateChartPeriod(period) {
    const statsData = period === 7 ? dailyStats : monthlyStats;

    if (!statsData || statsData.length === 0) {
        console.warn(`No data available for ${period}-day period`);
        return;
    }

    // グラフを再作成
    createChart(statsData, period);

    // アニメーションを追加
    const chartContainer = document.querySelector('.daily-stats-chart');
    if (chartContainer) {
        chartContainer.style.opacity = '0';
        chartContainer.style.transform = 'translateY(10px)';
        chartContainer.style.transition = 'opacity 0.3s ease, transform 0.3s ease';

        setTimeout(() => {
            chartContainer.style.opacity = '1';
            chartContainer.style.transform = 'translateY(0)';
        }, 50);
    }

    console.info(`Chart period updated to ${period} days`);
}

/**
 * 日付フォーマット
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    // 今日または昨日の場合は特別な表示
    if (date.toDateString() === today.toDateString()) {
        return '今日';
    } else if (date.toDateString() === yesterday.toDateString()) {
        return '昨日';
    }

    return `${month}/${day}`;
}

/**
 * 励ましメッセージの初期化
 */
function initializeEncouragementMessages() {
    const goalMessage = document.getElementById('goal-message');

    if (goalMessage && goalMessage.classList.contains('pending')) {
        // 未達成の場合の励ましメッセージをランダムに表示
        const messages = getEncouragementMessages();
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        goalMessage.textContent = randomMessage;

        // 一定時間ごとにメッセージを変更
        setInterval(() => {
            const newMessage = messages[Math.floor(Math.random() * messages.length)];
            goalMessage.style.opacity = '0';
            setTimeout(() => {
                goalMessage.textContent = newMessage;
                goalMessage.style.opacity = '1';
            }, 300);
        }, 10000); // 10秒ごとに変更
    }
}

/**
 * 励ましメッセージのリストを取得
 */
function getEncouragementMessages() {
    const remainingMinutes = parseInt(document.querySelector('.current-time')?.textContent || 0);
    const goalMinutes = parseInt(document.querySelector('.target-time')?.textContent || 0);

    const percentage = goalMinutes > 0 ? (remainingMinutes / goalMinutes) * 100 : 0;

    // 進捗に応じたメッセージ
    if (percentage >= 80) {
        return [
            'もう少し！目標達成まであと少し！',
            'あと一息！頑張って！',
            '目標まであと少し！ファイト！'
        ];
    } else if (percentage >= 50) {
        return [
            '半分以上達成！素晴らしい！',
            '順調に進んでいます！',
            'この調子で頑張りましょう！'
        ];
    } else if (percentage >= 20) {
        return [
            'スタートは順調！継続が大事！',
            '良いスタートを切りました！',
            'コツコツ続けましょう！'
        ];
    } else {
        return [
            '今日から始めましょう！',
            '最初の一歩が大切です！',
            '諦めないで！頑張りましょう！'
        ];
    }
}

/**
 * 目標更新機能（将来的な実装用）
 */
function updateGoal(newGoalMinutes) {
    // AJAXで目標を更新するエンドポイントを呼び出す
    fetch('/api/progress/update-goal/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            goal_minutes: newGoalMinutes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // ページをリロードして更新を反映
            location.reload();
        } else {
            console.error('目標更新に失敗しました:', data.error);
        }
    })
    .catch(error => {
        console.error('エラーが発生しました:', error);
    });
}

/**
 * CSRFトークンを取得
 */
function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}
