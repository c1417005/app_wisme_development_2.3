from django.forms import ModelForm
from django import forms
from .models import Page, CustomUser


class UserProfileForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['display_name', 'profile_image']


class PageForm(ModelForm):
    input_word = forms.CharField(
        label = "調べたい単語",
        widget = forms.TextInput(attrs={"id":"id_input_word"}),
        required = False)
    
    class Meta:
        model = Page
        fields = ["title","thoughts","page_date","picture"]