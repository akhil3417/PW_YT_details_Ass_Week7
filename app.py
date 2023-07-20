#!/usr/bin/env python3
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin
from googleapiclient.discovery import build
from bs4 import BeautifulSoup as bs
import requests
import logging

logging.basicConfig(filename="application.log", level=logging.INFO)

api_key = "API_HERE"

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
@cross_origin()
def home_page():
    return render_template('index.html')

def get_channel_id(youtube, input_link):
    response = requests.get(input_link)
    html = bs(response.text, 'html.parser')
    channel_link = html.find('meta', {'property': 'og:url'})['content']
    channel_id = channel_link.split('/')[-1]
    return channel_id

def get_playlist_id(youtube, channel_id):
    request = youtube.channels().list(
        part="contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()
    playlist_id = response['items'][0]["contentDetails"]["relatedPlaylists"]['uploads']
    return playlist_id

def get_video_ids(youtube, playlist_id):
    request = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=playlist_id
    )
    response = request.execute()
    video_ids = [video['contentDetails']['videoId'] for video in response['items']]
    return video_ids

def get_video_details(youtube, video_ids):
    request = youtube.videos().list(
        part='snippet,contentDetails,statistics',
        id=",".join(video_ids)
    )
    response = request.execute()
    video_details = []
    for video in response['items']:
        data = {
            'Title': video["snippet"]["title"],
            'Video_Link': "https://www.youtube.com/watch?v=" + video["id"],
            'Video_Thumbnails': video["snippet"]["thumbnails"]["standard"]["url"],
            'Views': video["statistics"]["viewCount"],
            'Posting_date': video["snippet"]["publishedAt"]
        }
        video_details.append(data)
    return video_details

@app.route('/details', methods=['GET', 'POST'])
@cross_origin()
def index():
    if request.method == 'POST':
        try:
            input_link = request.form['content']
            youtube = build('youtube', 'v3', developerKey=api_key)
            channel_id = get_channel_id(youtube, input_link)
            playlist_id = get_playlist_id(youtube, channel_id)
            video_ids = get_video_ids(youtube, playlist_id)
            video_details = get_video_details(youtube, video_ids)
            return render_template('result.html', details=video_details)
        except Exception as e:
            logging.info(e)
            return "Something went wrong"
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port="5004")
