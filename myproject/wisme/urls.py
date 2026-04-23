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
    path("words/", views.word_list, name="word_list"),
    path("words/<int:pk>/delete/", views.word_delete, name="word_delete"),
    path("quiz/", views.flashcard, name="flashcard"),
    path("profile/", views.profile, name="profile"),
    path("profile/update/", views.profile_update, name="profile_update"),
    path("books/thumbnail/", views.book_thumbnail_search, name="book_thumbnail_search"),
    path("feedback/submit/", views.feedback_submit, name="feedback_submit"),
]