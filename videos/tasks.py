import boto3
import subprocess
from celery import shared_task
from django.conf import settings
import os
from botocore.exceptions import BotoCoreError, ClientError

@shared_task
def process_video(video_path):
    #subtitle directory
    subtitles_path = f'{video_path}.srt'

    #extracting subtitles
    subprocess.run(['ccextractor', video_path, '-o', subtitles_path])

    #video output folder after adding subtitles
    output_folder = os.path.join(settings.MEDIA_ROOT, 'output')
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, os.path.basename(video_path))

    #embedding subtitles
    subprocess.run(['ffmpeg', '-i', video_path, '-i', subtitles_path, '-c', 'copy', '-c:s', 'mov_text', output_file])

    #uploading video
    s3_key = os.path.basename(output_file) 
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(output_file, settings.AWS_STORAGE_BUCKET_NAME, s3_key)
    except (BotoCoreError, ClientError) as e:
        print(f"Error uploading video to S3: {e}")
        return


    #for video link 

    s3_base_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.ap-south-1.amazonaws.com/"
    video_link = f"{s3_base_url}{s3_key}"
    
    subtitles = load_subtitles(subtitles_path=subtitles_path)
    store_subtitles_in_dynamodb(subtitles=subtitles, video_link=video_link, table_name=settings.DYNAMODB_TABLE_NAME)

    
    # Deleting all files after uploading
    for file_path in [video_path, subtitles_path, output_file]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                print(f"Error deleting file {file_path}: {e}") 

def load_subtitles(subtitles_path):
    subtitles = []
    start_time = None
    end_time = None
    with open(subtitles_path, 'r') as file:
        subtitle_text = []
        for line in file:
            line = line.strip()
            if '-->' in line:
                if start_time and subtitle_text:
                    subtitles.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'subtitle': ' '.join(subtitle_text)
                    })
                    subtitle_text = []
                start_time, end_time = line.split(' --> ')
            elif line.isdigit():
                continue
            else:
                subtitle_text.append(line)
        
        if start_time and subtitle_text:
            subtitles.append({
                'start_time': start_time,
                'end_time': end_time,
                'subtitle': ' '.join(subtitle_text)
            })

    return subtitles

def store_subtitles_in_dynamodb(subtitles, video_link, table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    for subtitle in subtitles:
        try:
            table.put_item(
                Item={
                    'video_link': video_link,
                    'start_time': subtitle['start_time'],
                    'end_time': subtitle['end_time'],
                    'subtitles': subtitle['subtitle']
                }
            )
        except Exception as e:
            print(f"Error adding subtitle: {subtitle['subtitle']}, Error: {e}")

