from django import forms
from .models import Discussion

class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ['question']
        widgets = {
            'question': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Posez votre question ici...'}),
        }
