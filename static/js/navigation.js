/**
 * VirtuTune - Mobile Navigation
 *
 * モバイルナビゲーションの制御ロジック
 */

(function() {
    'use strict';

    // DOM要素の取得
    const navbarToggle = document.querySelector('.navbar-toggle');
    const navbarMobileMenu = document.querySelector('.navbar-mobile-menu');
    const navbarOverlay = document.querySelector('.navbar-overlay');
    const navbarLinks = document.querySelectorAll('.navbar-link');

    /**
     * モバイルメニューを開く
     */
    function openMenu() {
        if (navbarToggle) {
            navbarToggle.classList.add('active');
        }
        if (navbarMobileMenu) {
            navbarMobileMenu.classList.add('active');
        }
        if (navbarOverlay) {
            navbarOverlay.classList.add('active');
        }
        // スクロールを防止
        document.body.style.overflow = 'hidden';
    }

    /**
     * モバイルメニューを閉じる
     */
    function closeMenu() {
        if (navbarToggle) {
            navbarToggle.classList.remove('active');
        }
        if (navbarMobileMenu) {
            navbarMobileMenu.classList.remove('active');
        }
        if (navbarOverlay) {
            navbarOverlay.classList.remove('active');
        }
        // スクロールを再有効化
        document.body.style.overflow = '';
    }

    /**
     * メニューの開閉をトグル
     */
    function toggleMenu() {
        const isOpen = navbarMobileMenu && navbarMobileMenu.classList.contains('active');
        if (isOpen) {
            closeMenu();
        } else {
            openMenu();
        }
    }

    /**
     * イベントリスナーの設定
     */
    function initEventListeners() {
        // ハンバーガーボタンのクリック
        if (navbarToggle) {
            navbarToggle.addEventListener('click', toggleMenu);
        }

        // オーバーレイのクリックでメニューを閉じる
        if (navbarOverlay) {
            navbarOverlay.addEventListener('click', closeMenu);
        }

        // メニューリンクのクリックでメニューを閉じる
        navbarLinks.forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // ESCキーでメニューを閉じる
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeMenu();
            }
        });

        // ウィンドウサイズ変更時、モバイルメニューを閉じる
        let resizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(() => {
                if (window.innerWidth > 767) {
                    closeMenu();
                }
            }, 250);
        });
    }

    /**
     * アクティブなページのハイライト
     */
    function highlightActivePage() {
        const currentPath = window.location.pathname;

        navbarLinks.forEach(link => {
            const linkPath = new URL(link.href).pathname;

            // 完全一致または親パスの一致
            if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath + '/'))) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    /**
     * 初期化
     */
    function init() {
        initEventListeners();
        highlightActivePage();
    }

    // DOMが読み込まれたら初期化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
