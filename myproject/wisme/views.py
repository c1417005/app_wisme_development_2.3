from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .forms import PageForm, UserProfileForm
from .models import Page, SearchedWord, CustomUser
from django.http import JsonResponse
from .utils.func_api import GeminiAsk

class IndexView(LoginRequiredMixin, View):
    def get(self,request):
        return render(request,"wisme/index.html")


class PageCreateView(LoginRequiredMixin, View):
    def get(self,request):
        form = PageForm()
        return render(request,"wisme/page_form.html",{"form":form})

    def post(self,request):
        form = PageForm(request.POST,request.FILES)
        if form.is_valid():
            new_page = form.save(commit=False)
            new_page.owner = request.user
            new_page.save()
            SearchedWord.objects.filter(note__isnull = True).update(note = new_page)
            return redirect("wisme:index")
        return render(request,"wisme/page_form.html",{"form":form})

class PageListView(LoginRequiredMixin, View):
    def get(self,request):
        page_list = Page.objects.filter(owner=request.user).order_by("-page_date")
        return render(request,"wisme/page_list.html",{"page_list":page_list})


class PageDetailView(LoginRequiredMixin, View):
    def get(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        words = page.words.all()
        contents = {
            "page":page,
            "words":words
        }
        return render(request,"wisme/page_detail.html",contents)

class PageUpdateView(LoginRequiredMixin, View):
    def get(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        form = PageForm(instance = page)
        words = page.words.all()
        contents = {
            "form":form,
            "words":words
        }
        return render(request,"wisme/page_update.html",contents)

    def post(self,request,id):
        page = get_object_or_404(Page, id=id, owner=request.user)
        form = PageForm(request.POST,request.FILES,instance=page)
        if form.is_valid():
            form.save()
            SearchedWord.objects.filter(note__isnull = True).update(note = page)
            return redirect("wisme:page_detail",id = id)
        return render(request,"wisme/page_form.html",{"form":form})


class PageSendWordReturnMean(LoginRequiredMixin, View):
    def get(self, request):
        word = request.GET.get('word')
        result =  GeminiAsk(word)
        SearchedWord.objects.create(
            word = word,
            meaning = result,
            note = None
        )
        data = {'meaning': f"{result}"}
        return JsonResponse(data)


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
profile = UserProfileView.as_view()
profile_update = UserProfileUpdateView.as_view()
