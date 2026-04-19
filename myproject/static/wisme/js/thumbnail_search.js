(() => {
  const toggleBtn   = document.getElementById('thumbnail-search-toggle');
  const panel       = document.getElementById('thumbnail-search-panel');
  const searchBtn   = document.getElementById('thumbnail-search-btn');
  const resultsEl   = document.getElementById('thumbnail-results');
  const imageUrlInput = document.getElementById('id_image_url');
  const previewWrap = document.getElementById('thumbnail-preview');
  const previewImg  = document.getElementById('thumbnail-preview-img');
  const clearBtn    = document.getElementById('thumbnail-clear-btn');

  if (!toggleBtn) return;

  toggleBtn.addEventListener('click', () => {
    panel.classList.toggle('hidden');
    resultsEl.classList.add('hidden');
  });

  searchBtn.addEventListener('click', async () => {
    const titleEl = document.getElementById('id_title');
    const authorEl = document.getElementById('thumbnail-author');
    const title = titleEl?.value?.trim() ?? '';
    const author = authorEl?.value?.trim() ?? '';
    if (!title) {
      titleEl?.focus();
      return;
    }

    resultsEl.innerHTML = '<p class="col-span-5 text-center text-xs text-stone-400 py-4 animate-pulse">検索中...</p>';
    resultsEl.classList.remove('hidden');

    try {
      const params = new URLSearchParams({ title, author });
      const res = await fetch(`/wisme/books/thumbnail/?${params}`);
      const data = await res.json();

      if (!data.results || data.results.length === 0) {
        resultsEl.innerHTML = '<p class="col-span-5 text-center text-xs text-stone-400 py-4">見つかりませんでした</p>';
        return;
      }

      resultsEl.innerHTML = data.results.map(book => `
        <button type="button"
                class="thumbnail-candidate group text-left focus:outline-none"
                data-url="${escapeAttr(book.thumbnail)}">
          <div class="aspect-[2/3] rounded-lg overflow-hidden border-2 border-transparent group-hover:border-accent-400 group-focus:border-accent-500 transition-all shadow-sm">
            <img src="${escapeAttr(book.thumbnail)}"
                 alt="${escapeAttr(book.title)}"
                 class="w-full h-full object-cover"
                 onerror="this.parentElement.innerHTML='<div class=\'w-full h-full bg-stone-100 flex items-center justify-center\'><span class=\'text-stone-300 text-xs\'>No image</span></div>'">
          </div>
          <p class="text-xs text-stone-500 mt-1 line-clamp-2 leading-tight">${escapeHtml(book.title)}</p>
        </button>
      `).join('');

      resultsEl.querySelectorAll('.thumbnail-candidate').forEach(btn => {
        btn.addEventListener('click', () => selectThumbnail(btn.dataset.url));
      });
    } catch {
      resultsEl.innerHTML = '<p class="col-span-5 text-center text-xs text-red-400 py-4">エラーが発生しました</p>';
    }
  });

  clearBtn?.addEventListener('click', () => {
    imageUrlInput.value = '';
    previewWrap.classList.add('hidden');
    previewImg.src = '';
  });

  function selectThumbnail(url) {
    imageUrlInput.value = url;
    previewImg.src = url;
    previewWrap.classList.remove('hidden');
    panel.classList.add('hidden');
    resultsEl.classList.add('hidden');
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function escapeAttr(str) {
    return String(str).replace(/"/g, '&quot;');
  }
})();
