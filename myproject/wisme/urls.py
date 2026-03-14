from django.urls import path
from . import views

app_name = "wisme"

urlpatterns = [
    path("",views.index,name = "index"),
    path("page/create/",views.page_create,name = "page_create"),
    path("page/list/",views.page_list,name = "page_list"),
    path("page/<uuid:id>/",views.page_detail,name = "page_detail"),
    path("page/<uuid:id>/update/",views.page_update,name = "page_update"),
    path("page/<uuid:id>/delete/",views.page_delete,name = "page_delete"),
    path("search/mean/",views.page_return_mean,name = "page_return_mean"),
]