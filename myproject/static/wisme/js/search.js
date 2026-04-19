// 単語検索パネル初期化 — desktop / mobile の両パネルをそれぞれ独立セットアップする
document.addEventListener('DOMContentLoaded', function () {
    ['desktop', 'mobile'].forEach(setupPanel);
});

function setupPanel(prefix) {
    const input     = document.getElementById(`${prefix}-word-input`);
    const btn       = document.getElementById(`${prefix}-search-btn`);
    const skeleton  = document.getElementById(`${prefix}-skeleton`);
    const results   = document.getElementById(`${prefix}-results`);
    const indicator = document.getElementById(`${prefix}-indicator`);

    if (!btn || !input) return;

    btn.addEventListener('click', doSearch);
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });

    async function doSearch() {
        const word = input.value.trim();
        if (!word) return;

        skeleton.classList.remove('hidden');
        indicator.classList.add('hidden');
        indicator.classList.remove('flex');

        const csrfEl = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfEl ? csrfEl.value : '';

        try {
            const res = await fetch(`/wisme/search/mean/?word=${encodeURIComponent(word)}`, {
                headers: { 'X-CSRFToken': csrfToken }
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            appendResult(word, data.meaning);

            indicator.classList.remove('hidden');
            indicator.classList.add('flex');
            lucide.createIcons();
            setTimeout(() => {
                indicator.classList.add('hidden');
                indicator.classList.remove('flex');
            }, 3000);

            input.value = '';
        } catch (err) {
            console.error('Word search error:', err);
            appendError();
        } finally {
            skeleton.classList.add('hidden');
        }
    }

    function appendResult(word, meaning) {
        const card = document.createElement('div');
        card.className = 'bg-stone-50 rounded-xl p-3 pr-7 relative border-l-2 border-accent-300';
        card.innerHTML = `
            <p class="font-semibold text-accent-700 text-sm mb-1">${escHtml(word)}</p>
            <p class="text-xs text-stone-500 leading-relaxed">${escHtml(meaning)}</p>
            <button class="absolute top-2 right-2 text-stone-300 hover:text-stone-500 transition-colors"
                    onclick="this.closest('div').remove()" title="非表示">
                <i data-lucide="x" class="w-3.5 h-3.5"></i>
            </button>`;
        results.prepend(card);
        lucide.createIcons();
    }

    function appendError() {
        const el = document.createElement('p');
        el.className = 'text-xs text-red-400 py-1';
        el.textContent = '検索に失敗しました。再度お試しください。';
        results.prepend(el);
        setTimeout(() => el.remove(), 4000);
    }
}

function escHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
