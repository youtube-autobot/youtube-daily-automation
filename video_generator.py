#!/usr/bin/env python3
import os
import random
import requests
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap
import subprocess

class AutoVideoCreator:
    def __init__(self):
        self.templates = [
            self.create_motivational_short,
            self.create_facts_video,
            self.create_countdown_video
        ]
        
    def get_daily_content(self):
        """Get fresh content from free APIs"""
        try:
            # Get motivational quote
            quote_data = requests.get("https://api.quotable.io/random").json()
            return {
                'type': 'quote',
                'text': f"{quote_data['content']}\n\n- {quote_data['author']}",
                'hashtags': '#motivation #inspiration #success'
            }
        except:
            # Fallback content
            fallback_quotes = [
                "The only way to do great work is to love what you do. - Steve Jobs",
                "Your time is limited, so don't waste it living someone else's life. - Steve Jobs",
                "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt"
            ]
            return {
                'type': 'quote',
                'text': random.choice(fallback_quotes),
                'hashtags': '#daily #viral #shorts'
            }
    
    def create_motivational_short(self, content):
        """Create 60-second motivational video"""
        # Create image with text
        img = Image.new('RGB', (1080, 1920), color=(10, 10, 30))
        draw = ImageDraw.Draw(img)
        
        try:
            # Try to use Arial font, fallback to default
            font = ImageFont.truetype("Arial", 70)
        except:
            font = ImageFont.load_default()
        
        # Wrap and center text
        wrapped_text = textwrap.fill(content['text'], width=30)
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[0]
        
        position = ((1080 - text_width) // 2, (1920 - text_height) // 2)
        
        draw.text(position, wrapped_text, fill=(255, 215, 0), font=font)
        
        # Save image
        img.save("daily_content.png")
        
        # Create video from image (5 seconds for testing, change to 60 for real)
        self.create_video_from_image("daily_content.png", "output_video.mp4", duration=5)
        
        return "output_video.mp4"
    
    def create_video_from_image(self, image_path, output_path, duration=5):
        """Convert image to video with fade effects"""
        # Simple ffmpeg command to create video from image
        cmd = [
            'ffmpeg',
            '-loop', '1',
            '-i', image_path,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-vf', f'fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1',
            output_path,
            '-y'
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            print(f"Video created: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr}")
            # Create a simple fallback video
            self.create_fallback_video(output_path)
    
    def create_fallback_video(self, output_path):
        """Create a simple colored video if FFmpeg fails"""
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'color=c=blue:s=1080x1920:d=5',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            output_path,
            '-y'
        ]
        subprocess.run(cmd, capture_output=True)
    
    def create_facts_video(self, content):
        """Create facts video"""
        return self.create_motivational_short(content)
    
    def create_countdown_video(self, content):
        """Create countdown video"""
        return self.create_motivational_short(content)
    
    def run_daily(self):
        """Main function - runs automatically"""
        print(f"[{datetime.now()}] Starting daily video creation...")
        
        # Get fresh content
        content = self.get_daily_content()
        print(f"Content: {content['text'][:50]}...")
        
        # Pick random template
        video_creator = random.choice(self.templates)
        
        # Create video
        video_file = video_creator(content)
        
        # Generate metadata
        metadata = {
            'video_file': video_file,
            'title': self.generate_title(content),
            'description': self.generate_description(content),
            'tags': ['shorts', 'viral', 'daily', 'motivation']
        }
        
        # Save metadata to file
        with open("video_info.txt", "w") as f:
            f.write(f"TITLE: {metadata['title']}\n")
            f.write(f"DESCRIPTION: {metadata['description']}\n")
            f.write(f"TAGS: {','.join(metadata['tags'])}\n")
            f.write(f"FILE: {metadata['video_file']}\n")
        
        print(f"[{datetime.now()}] Video created: {metadata['video_file']}")
        return metadata
    
    def generate_title(self, content):
        """Generate clickable titles"""
        templates = [
            f"This Will Change Your Perspective",
            f"Daily Wisdom {datetime.now().strftime('%m/%d/%Y')}",
            f"The Truth Nobody Tells You",
            f"One Minute That Could Change Everything"
        ]
        return random.choice(templates)
    
    def generate_description(self, content):
        """Auto-generate YouTube description"""
        date_str = datetime.now().strftime("%B %d, %Y")
        hashtags = content.get('hashtags', '#shorts #viral #daily')
        
        return f"""{content['text']}

📅 Daily upload for {date_str}
🔥 New video every day at 2 PM UTC

{hashtags}

#shorts #viral #trending #motivation #inspiration #success #mindset 
#daily #youtube #subscribe #like #comment

▶️ Watch our previous videos
🔔 Turn on notifications
👍 Like if you enjoyed

This content is automatically generated.
"""

if __name__ == "__main__":
    creator = AutoVideoCreator()
    result = creator.run_daily()
    
    # Print result for debugging
    print(f"Title: {result['title']}")
    print(f"Video file: {result['video_file']}")
