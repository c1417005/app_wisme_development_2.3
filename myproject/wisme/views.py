from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.views.generic import ListView
from django.urls import reverse_lazy, reverse
from .forms import PageForm, UserProfileForm, ChapterFormSet, FeedbackForm
from .models import Page, SearchedWord, CustomUser
from django.http import JsonResponse
from .services import WordService, BookThumbnailService

class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        pages = Page.objects.filter(owner=request.user)
        latest = pages.order_by('-update_at').first()
        ctx = {
            'page_count': pages.count(),
            'latest_page': latest,
            'last_updated_at': latest.update_at.isoformat() if latest else '',
            'feedback_form': FeedbackForm(),
            'feedback_sent': request.GET.get('feedback') == 'sent',
        }
        return render(request, "wisme/index.html", ctx)


class FeedbackSubmitView(LoginRequiredMixin, View):
    def post(self, request):
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.owner = request.user
            feedback.save()
            return redirect(reverse('wisme:index') + '?feedback=sent')
        return redirect('wisme:index')


class PageCreateView(LoginRequiredMixin, View):
    def get(self,request):
        form = PageForm()
        chapter_formset = ChapterFormSet()
        return render(request,"wisme/page_form.html",{"form":form,"chapter_formset":chapter_formset})

    def post(self,request):
        form = PageForm(request.POST,request.FILES)
        chapter_formset = ChapterFormSet(request.POST)
        if form.is_valid() and chapter_formset.is_valid():
            new_page = form.save(commit=False)
            new_page.owner = request.user
            new_page.save()
            chapter_formset.instance = new_page
            chapters = chapter_formset.save(commit=False)
            for idx, chapter in enumerate(chapters):
                chapter.order = idx
                chapter.save()
            for obj in chapter_formset.deleted_objects:
                obj.delete()
            SearchedWord.objects.filter(note__isnull = True).update(note = new_page)
            return redirect("wisme:index")
        return render(request,"wisme/page_form.html",{"form":form,"chapter_formset":chapter_formset})

class PageListView(LoginRequiredMixin, View):
    def get(self,request):
        page_list = Page.objects.filter(owner=request.user).order_by("-page_date")
        return render(request,"wisme/page_list.html",{"page_list":page_list})


class PageDetailView(LoginRequiredMixin, View):
    def get(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        words = page.words.all()
        chapters = page.chapters.all()
        contents = {
            "page":page,
            "words":words,
            "chapters":chapters,
        }
        return render(request,"wisme/page_detail.html",contents)

class PageUpdateView(LoginRequiredMixin, View):
    def get(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        form = PageForm(instance = page)
        chapter_formset = ChapterFormSet(instance=page)
        words = page.words.all()
        contents = {
            "form":form,
            "chapter_formset":chapter_formset,
            "words":words,
        }
        return render(request,"wisme/page_update.html",contents)

    def post(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        form = PageForm(request.POST,request.FILES,instance=page)
        chapter_formset = ChapterFormSet(request.POST,instance=page)
        if form.is_valid() and chapter_formset.is_valid():
            form.save()
            chapters = chapter_formset.save(commit=False)
            for idx, chapter in enumerate(chapters):
                chapter.order = idx
                chapter.save()
            for obj in chapter_formset.deleted_objects:
                obj.delete()
            SearchedWord.objects.filter(note__isnull = True).update(note = page)
            return redirect("wisme:page_detail",id = id)
        words = page.words.all()
        return render(request,"wisme/page_update.html",{"form":form,"chapter_formset":chapter_formset,"words":words})


class BookThumbnailSearchView(LoginRequiredMixin, View):
    def get(self, request):
        title = request.GET.get('title', '').strip()
        author = request.GET.get('author', '').strip()
        if not title:
            return JsonResponse({'results': []})
        results = BookThumbnailService.search(title, author)
        return JsonResponse({'results': results})


class PageSendWordReturnMean(LoginRequiredMixin, View):
    def get(self, request):
        word = request.GET.get('word')
        instance = WordService.search_or_fetch(word, user=request.user)
        return JsonResponse({'meaning': instance.meaning})


class PageDeleteView(LoginRequiredMixin, View):
    def get(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        words = page.words.all()
        contents = {
            "page":page,
            "words":words
        }
        return render(request,"wisme/page_confirm_delete.html",contents)

    def post(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        page.delete()
        return redirect('wisme:page_list')



        



class WordListView(LoginRequiredMixin, ListView):
    model = SearchedWord
    template_name = 'wisme/word_list.html'
    context_object_name = 'words'

    def get_queryset(self):
        qs = SearchedWord.objects.filter(owner=self.request.user).select_related('note')
        if self.request.GET.get('sort') == 'alpha':
            return qs.order_by('word')
        return qs.order_by('-created_at')


class WordDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        word = get_object_or_404(SearchedWord, pk=pk, owner=request.user)
        word.owner = None
        word.note = None
        word.save(update_fields=['owner', 'note'])
        return redirect('wisme:word_list')


class FlashcardView(LoginRequiredMixin, ListView):
    model = SearchedWord
    template_name = 'wisme/flashcard.html'
    context_object_name = 'words'

    def get_queryset(self):
        qs = SearchedWord.objects.filter(owner=self.request.user).select_related('note')
        if self.request.GET.get('sort') == 'alpha':
            return qs.order_by('word')
        return qs.order_by('-created_at')


class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'wisme/profile.html', {'user': request.user})


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'wisme/profile_update.html'
    success_url = reverse_lazy('wisme:profile')

    def get_object(self):
        return self.request.user


index = IndexView.as_view()
page_create = PageCreateView.as_view()
page_list = PageListView.as_view()
page_detail = PageDetailView.as_view()
page_update = PageUpdateView.as_view()
page_delete = PageDeleteView.as_view()
page_return_mean = PageSendWordReturnMean.as_view()
word_list = WordListView.as_view()
word_delete = WordDeleteView.as_view()
flashcard = FlashcardView.as_view()
profile = UserProfileView.as_view()
profile_update = UserProfileUpdateView.as_view()
book_thumbnail_search = BookThumbnailSearchView.as_view()
feedback_submit = FeedbackSubmitView.as_view()
