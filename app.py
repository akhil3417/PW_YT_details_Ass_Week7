#Required libraries
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS,cross_origin
from googleapiclient.discovery import build
from bs4 import BeautifulSoup as bs
import requests
import pymongo
import logging

#Create a logging file
logging.basicConfig(filename="application.log", level=logging.INFO)

#Setup API key, Channel ID
api_key = "AIzaSyCpdCJguhqI0aPRgTcGpfkgMzk7elszDUU"

#Create api service
youtube = build('youtube','v3', developerKey= api_key)

#setup a flask
app = Flask(__name__)

#Create a the homepage
@app.route('/', methods = ['GET'])
def home_page():
    return render_template('index.html')

#extract details
@app.route('/details', methods = ['GET','POST'])
def index():
    if request.method == 'POST':
        try:
            #Get channel ID with beautifulSoup
            input_link = request.form['content']
            response = requests.get(input_link)
            html = bs(response.text, 'html.parser')

            #Extract channel link with channel_id 
            channel_link = html.find_all('meta', {'property':"og:url"})[0]['content']

            #Extract Channel ID
            channel_ID = channel_link.split('/')[-1]

            #Function for channel details 
            def get_channel_details(youtube, channel_ID):
                request = youtube.channels().list(
                    part="contentDetails,statistics",
                    id= channel_ID)
                response = request.execute()
                playlist_id = response['items'][0]["contentDetails"]["relatedPlaylists"]['uploads']
                return playlist_id
            
            #Extract Playlist ID
            playlist_id = get_channel_details(youtube, channel_ID)

            # Function for extract first 5 videos
            def get_videos_list(youtube, playlist_id):
                request = youtube.playlistItems().list(
                    part = 'contentDetails',
                    playlistId = playlist_id)
                response = request.execute()

                video_ids = []
                for video in response['items']:
                    video_id = video['contentDetails']['videoId']
                    video_ids.append(video_id)

                return video_ids
            
            #Extract Video ID
            video_ids = get_videos_list(youtube, playlist_id)

            #Function for extract videos details
            #Function for extract videos details
            def get_video_details(youtube, video_ids):
                request = youtube.videos().list(
                    part = 'snippet,contentDetails,statistics',
                    id = ",".join(video_ids))
                            
                response = request.execute()

                video_details =[]
                for video in response['items']:
                    data = dict(Title = video["snippet"]["title"],
                            Video_Link = "https://www.youtube.com/watch?v=" + video["id"], 
                            Video_Thumbnails = video["snippet"]["thumbnails"]["standard"]["url"],
                            Views= video["statistics"]["viewCount"],
                            Posting_date= video["snippet"]["publishedAt"])
                    video_details.append(data)
                return video_details
            
            #Get Video details
            video_details = get_video_details(youtube, video_ids)

            #Showing Result on Web Page
            return render_template('result.html', details = video_details[0:len(video_details)-1]) 
        except Exception as e:
            logging.info(e)
            return "somthing went wrong"
    
    else:
        return render_template('index.html')
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port="5004")