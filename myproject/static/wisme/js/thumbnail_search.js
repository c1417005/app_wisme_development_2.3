(() => {
  const toggleBtn      = document.getElementById('thumbnail-search-toggle');
  const panel          = document.getElementById('thumbnail-search-panel');
  const searchBtn      = document.getElementById('thumbnail-search-btn');
  const resultsWrapper = document.getElementById('thumbnail-results-wrapper');
  const resultsEl      = document.getElementById('thumbnail-results');
  const prevBtn        = document.getElementById('thumbnail-prev-btn');
  const nextBtn        = document.getElementById('thumbnail-next-btn');
  const pageInfo       = document.getElementById('thumbnail-page-info');
  const imageUrlInput  = document.getElementById('id_image_url');
  const previewWrap    = document.getElementById('thumbnail-preview');
  const previewImg     = document.getElementById('thumbnail-preview-img');
  const clearBtn       = document.getElementById('thumbnail-clear-btn');

  if (!toggleBtn) return;

  const PAGE_SIZE = 5;
  let allResults  = [];
  let currentPage = 0;

  toggleBtn.addEventListener('click', () => {
    panel.classList.toggle('hidden');
    resultsWrapper.classList.add('hidden');
  });

  searchBtn.addEventListener('click', async () => {
    const titleEl  = document.getElementById('id_title');
    const authorEl = document.getElementById('thumbnail-author');
    const title    = titleEl?.value?.trim() ?? '';
    const author   = authorEl?.value?.trim() ?? '';
    if (!title) { titleEl?.focus(); return; }

    resultsEl.innerHTML = '<p class="col-span-5 text-center text-xs text-stone-400 py-4 animate-pulse">検索中...</p>';
    resultsWrapper.classList.remove('hidden');
    prevBtn.classList.add('hidden');
    nextBtn.classList.add('hidden');
    pageInfo.classList.add('hidden');

    try {
      const params = new URLSearchParams({ title, author });
      const res    = await fetch(`/wisme/books/thumbnail/?${params}`);
      const data   = await res.json();

      if (!data.results || data.results.length === 0) {
        resultsEl.innerHTML = '<p class="col-span-5 text-center text-xs text-stone-400 py-4">見つかりませんでした</p>';
        return;
      }

      allResults  = data.results;
      currentPage = 0;
      renderPage();
    } catch {
      resultsEl.innerHTML = '<p class="col-span-5 text-center text-xs text-red-400 py-4">エラーが発生しました</p>';
    }
  });

  prevBtn.addEventListener('click', () => {
    if (currentPage > 0) { currentPage--; renderPage(); }
  });

  nextBtn.addEventListener('click', () => {
    const totalPages = Math.ceil(allResults.length / PAGE_SIZE);
    if (currentPage < totalPages - 1) { currentPage++; renderPage(); }
  });

  function renderPage() {
    const totalPages = Math.ceil(allResults.length / PAGE_SIZE);
    const start      = currentPage * PAGE_SIZE;
    const pageItems  = allResults.slice(start, start + PAGE_SIZE);

    resultsEl.innerHTML = pageItems.map(book => `
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

    if (totalPages <= 1) {
      prevBtn.classList.add('hidden');
      nextBtn.classList.add('hidden');
      pageInfo.classList.add('hidden');
    } else {
      prevBtn.classList.remove('hidden');
      nextBtn.classList.remove('hidden');
      prevBtn.disabled = currentPage === 0;
      nextBtn.disabled = currentPage >= totalPages - 1;
      pageInfo.textContent = `${currentPage + 1} / ${totalPages}`;
      pageInfo.classList.remove('hidden');
    }
  }

  clearBtn?.addEventListener('click', () => {
    imageUrlInput.value = '';
    previewWrap.classList.add('hidden');
    previewImg.src = '';
  });

  function selectThumbnail(url) {
    imageUrlInput.value = url;
    previewImg.src      = url;
    previewWrap.classList.remove('hidden');
    panel.classList.add('hidden');
    resultsWrapper.classList.add('hidden');
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
