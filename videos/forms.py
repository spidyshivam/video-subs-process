from django import forms

class SubtitleSearchForm(forms.Form):
    query = forms.CharField(label='Search Subtitles', max_length=100)

class VideoUploadForm(forms.Form):
    video = forms.FileField()