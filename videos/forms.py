from django import forms

class SubtitleSearchForm(forms.Form):
    query = forms.CharField(label='Search Subtitles', max_length=100)
