// 章 formset の動的追加・削除を管理する
// - 「章を追加」ボタンで empty_form を複製し __prefix__ を TOTAL_FORMS に置換
// - 「×」ボタンで DELETE チェックをオンにして非表示にする（既存章の場合）
//   or DOM から除去する（新規追加の未保存章の場合）
document.addEventListener('DOMContentLoaded', function () {
    const list       = document.getElementById('chapter-list');
    const addBtn     = document.getElementById('add-chapter-btn');
    const template   = document.getElementById('chapter-empty-template');
    const totalInput = document.querySelector('input[name="chapters-TOTAL_FORMS"]');

    if (!list || !addBtn || !template || !totalInput) return;

    addBtn.addEventListener('click', () => {
        const index = parseInt(totalInput.value, 10);
        const html  = template.innerHTML.replace(/__prefix__/g, index);

        const wrapper = document.createElement('div');
        wrapper.innerHTML = html.trim();
        const node = wrapper.firstElementChild;
        list.appendChild(node);

        totalInput.value = index + 1;

        renumberChapters();
        if (window.lucide) lucide.createIcons();
    });

    // 既存章・新規章どちらも「×」で削除対応
    list.addEventListener('click', (e) => {
        const btn = e.target.closest('.chapter-remove');
        if (!btn) return;
        const item = btn.closest('.chapter-item');
        if (!item) return;

        const deleteInput = item.querySelector('input[type="checkbox"][name$="-DELETE"]');
        const idInput     = item.querySelector('input[type="hidden"][name$="-id"]');

        if (deleteInput && idInput && idInput.value) {
            // 既存章: DELETE にチェックして非表示化
            deleteInput.checked = true;
            item.classList.add('hidden');
        } else {
            // 新規追加の未保存章: DOM から除去し TOTAL_FORMS を戻す
            item.remove();
            totalInput.value = Math.max(0, parseInt(totalInput.value, 10) - 1);
        }

        renumberChapters();
    });

    function renumberChapters() {
        const visible = list.querySelectorAll('.chapter-item:not(.hidden)');
        visible.forEach((el, i) => {
            const label = el.querySelector('.chapter-number');
            if (label) label.textContent = `第${i + 1}章`;
        });
    }
});
