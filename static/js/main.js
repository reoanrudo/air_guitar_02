/**
 * VirtuTune - Main JavaScript
 *
 * メインのJavaScriptファイル
 */

(function() {
    'use strict';

    /**
     * アプリケーション初期化
     */
    function init() {
        console.log('VirtuTune initialized');
    }

    // DOM読み込み完了時に初期化を実行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
