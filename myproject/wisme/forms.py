from django.forms import ModelForm, inlineformset_factory
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Page, Chapter, CustomUser, Feedback


class UserProfileForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['display_name', 'profile_image']


class PageForm(ModelForm):
    input_word = forms.CharField(
        label = _("調べたい単語"),
        widget = forms.TextInput(attrs={"id":"id_input_word"}),
        required = False)

    class Meta:
        model = Page
        fields = ["title", "thoughts", "page_date", "picture", "image_url"]
        widgets = {
            'image_url': forms.HiddenInput(),
            'page_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ChapterForm(ModelForm):
    class Meta:
        model = Chapter
        fields = ['title', 'content', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': _('章タイトル（任意）')}),
            'content': forms.Textarea(attrs={'placeholder': _('この章の内容'), 'rows': 6}),
            'order': forms.HiddenInput(),
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': 2000,
                'placeholder': _('ご意見・ご要望・不具合報告などをお気軽にどうぞ'),
            }),
        }


ChapterFormSet = inlineformset_factory(
    Page,
    Chapter,
    form=ChapterForm,
    extra=1,
    can_delete=True,
)