#!/usr/bin/env python3
import os
import pickle
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import requests

class YouTubeAutoUploader:
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        
    def get_credentials(self):
        """Get credentials using environment variables (for GitHub Actions)"""
        client_id = os.environ.get("YOUTUBE_CLIENT_ID")
        client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            raise ValueError("Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET in environment")
        
        creds = None
        
        # Try to load existing token
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # First time - we need to get authorization code manually
                print("First time setup needed!")
                print("Please run the authentication manually first.")
                return None
            
            # Save credentials for next time
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
        
        return creds
    
    def upload_video(self, file_path, title, description, tags, category_id="22"):
        """Upload video to YouTube"""
        creds = self.get_credentials()
        if not creds:
            print("❌ No valid credentials. Authentication required.")
            return None
        
        youtube = build(self.api_service_name, self.api_version, credentials=creds)
        
        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": category_id
            },
            "status": {
                "privacyStatus": "private",  # Start with private for testing
                "selfDeclaredMadeForKids": False
            }
        }
        
        try:
            # Upload the video
            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            print(f"✅ Video uploaded successfully!")
            print(f"Video ID: {response['id']}")
            print(f"Title: {response['snippet']['title']}")
            
            # Change to public after successful upload
            video_id = response['id']
            youtube.videos().update(
                part="status",
                body={
                    "id": video_id,
                    "status": {
                        "privacyStatus": "public"
                    }
                }
            ).execute()
            print("✅ Video set to PUBLIC")
            
            return response
            
        except Exception as e:
            print(f"❌ Upload failed: {str(e)}")
            return None

def get_video_info():
    """Read video metadata from file"""
    video_info = {}
    try:
        with open("video_info.txt", "r") as f:
            for line in f:
                if ": " in line:
                    key, value = line.strip().split(": ", 1)
                    video_info[key] = value
        return video_info
    except FileNotFoundError:
        print("❌ video_info.txt not found. Run video_generator.py first.")
        return None

def manual_auth_first_time():
    """First-time authentication helper"""
    print("\n" + "="*60)
    print("FIRST TIME AUTHENTICATION REQUIRED")
    print("="*60)
    print("\nTo get your refresh token, follow these steps:")
    print("\n1. Go to this URL in your browser (replace CLIENT_ID):")
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    auth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={client_id}&redirect_uri=http://localhost:8080/&response_type=code&scope=https://www.googleapis.com/auth/youtube.upload&access_type=offline"
    print(f"   {auth_url}")
    print("\n2. Login with your YouTube account and allow access")
    print("3. You'll be redirected to localhost (will show error)")
    print("4. Copy the ENTIRE URL from the address bar")
    print("5. Look for 'code=' in the URL and copy that code")
    print("\nExample URL: http://localhost:8080/?code=4/0ATh...")
    print("Copy the code after 'code=' (everything until &)")
    print("="*60)
    return input("\nPaste the code here: ").strip()

def exchange_code_for_token(code):
    """Exchange authorization code for refresh token"""
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:8080/'
    }
    
    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        refresh_token = tokens.get('refresh_token')
        
        if refresh_token:
            # Save refresh token to file for GitHub Actions
            with open("refresh_token.txt", "w") as f:
                f.write(refresh_token)
            print(f"✅ Refresh token saved: {refresh_token[:20]}...")
            
            # Also save as pickle for local use
            from google.oauth2.credentials import Credentials
            creds = Credentials(
                token=tokens.get('access_token'),
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                scopes=["https://www.googleapis.com/auth/youtube.upload"]
            )
            
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
            
            return True
        else:
            print("❌ No refresh token in response")
            return False
    else:
        print(f"❌ Token exchange failed: {response.text}")
        return False

if __name__ == "__main__":
    print("🚀 Starting YouTube Auto Uploader")
    
    # Check if first-time auth is needed
    if not os.path.exists("token.pickle"):
        print("\n🔐 First time setup detected")
        
        # Check if we have client credentials
        client_id = os.environ.get("YOUTUBE_CLIENT_ID")
        client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            print("❌ Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET")
            print("   Make sure they are set in GitHub Secrets")
            exit(1)
        
        print(f"Client ID: {client_id[:30]}...")
        
        # Ask user to manually authenticate
        auth_code = manual_auth_first_time()
        if auth_code and exchange_code_for_token(auth_code):
            print("✅ Authentication successful! Ready to upload.")
        else:
            print("❌ Authentication failed")
            exit(1)
    
    # Get video metadata
    video_info = get_video_info()
    if not video_info:
        exit(1)
    
    # Upload video
    uploader = YouTubeAutoUploader()
    result = uploader.upload_video(
        file_path=video_info.get("FILE", "output_video.mp4"),
        title=video_info.get("TITLE", "Daily Video"),
        description=video_info.get("DESCRIPTION", ""),
        tags=video_info.get("TAGS", "").split(",")
    )
    
    if result:
        print("\n🎉 SUCCESS! Video is now live on YouTube")
        print(f"   https://youtube.com/watch?v={result['id']}")
    else:
        print("\n❌ Upload failed. Check errors above.")
