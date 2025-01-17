from django.shortcuts import render
import os
from django.conf import settings
from django.http import JsonResponse
import boto3
from videos.tasks import process_video
from .forms import SubtitleSearchForm, VideoUploadForm  # Import VideoUploadForm


def upload_view(request):
    form = VideoUploadForm(request.POST, request.FILES)  # Create form instance
    if form.is_valid():  # Check if form is valid
        video = form.cleaned_data['video']  # Get video from form
        input_folder = os.path.join(settings.MEDIA_ROOT, 'input')
        os.makedirs(input_folder, exist_ok=True)
        temp_path = os.path.join(input_folder, video.name)
        with open(temp_path, 'wb+') as destination:
            for chunk in video.chunks():
                destination.write(chunk)
        process_video.delay(temp_path)
        return render(request, 'upload_success.html')  # Render upload_success.html upon successful upload
    return render(request, 'upload.html', {'form': form})  # Pass form to template


def search_subtitles(request):
    form = SubtitleSearchForm()
    results = []
    
    if request.method == 'POST':
        form = SubtitleSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            dynamodb = boto3.resource(
                'dynamodb',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION_NAME
            )
            table = dynamodb.Table(settings.DYNAMODB_TABLE_NAME)

            # Scan DynamoDB table
            response = table.scan()
            items = response.get('Items', [])

            # Filter items containing the query in subtitles
            results = [
                item for item in items if query.lower() in item['subtitles'].lower()
            ]

    return render(request, 'search.html', {'form': form, 'results': results})