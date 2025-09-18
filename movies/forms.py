from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body", "parent"]
        widgets = {
            "parent": forms.HiddenInput(),   # we don’t show parent in the UI, just set it when replying
        }