from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from .forms import PageForm
from .models import Page,SearchedWord
from django.http import JsonResponse
from .utils.func_api import GeminiAsk
#.は今のフォルダ。つまりwismeを指す。アプリフォルダ内にutilsを作ったのでこの書き方。

class IndexView(View):
    def get(self,request):
        return render(request,"wisme/index.html")


class PageCreateView(View):
    def get(self,request):
        form = PageForm()
        return render(request,"wisme/page_form.html",{"form":form})

    def post(self,request):
        form = PageForm(request.POST,request.FILES)
        # if "research" in request.POST:
        #     print("success")
        if "reserve" in request.POST:
            if form.is_valid():
                form.save()
                return redirect("wisme:index")
            return render(request,"wisme/page_form.html",{"form":form})

class PageListView(View):
    def get(self,request):
        page_list = Page.objects.order_by("-page_date")
        return render(request,"wisme/page_list.html",{"page_list":page_list})
    

class PageDetailView(View):
    def get(self,request,id):
        page = get_object_or_404(Page,id = id)
        return render(request,"wisme/page_detail.html",{"page":page})
    

class PageUpdateView(View):
    def get(self,request,id):
        page = get_object_or_404(Page,id = id)
        form = PageForm(instance = page)
        return render(request,"wisme/page_update.html",{"form":form})
    
    def post(self,request,id):
        page = get_object_or_404(Page,id = id)
        form = PageForm(request.POST,request.FILES,instance=page)
        if form.is_valid():
            form.save()
            return redirect("wisme:page_detail",id = id)
        return render(request,"wisme/page_form.html",{"form":form})


class PageSendWordReturnMean(View):
    def get(self, request):
        word = request.GET.get('word')
        result =  GeminiAsk(word)
        SearchedWord.objects.create(
            input_word = word,
            return_mean = result,
            note = None
        )
        data = {'meaning': f"{result}"}
        return JsonResponse(data)
        

class PageDeleteView(View):
    def get(self,request,id):
        page = get_object_or_404(Page,id = id)
        return render(request,"wisme/page_confirm_delete.html",{"page":page})
    
    def post(self,request,id):
        page = get_object_or_404(Page,id = id)
        page.delete()
        return redirect('wisme:page_list')



        



index = IndexView.as_view()
page_create = PageCreateView.as_view()
page_list = PageListView.as_view()
page_detail = PageDetailView.as_view()
page_update = PageUpdateView.as_view()
page_delete = PageDeleteView.as_view()
page_return_mean = PageSendWordReturnMean.as_view()
