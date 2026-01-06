import logging
import os
import yt_dlp
from typing import Dict

logger = logging.getLogger(__name__)

class DownloadService:
    """Service for downloading YouTube videos using yt-dlp"""
    
    def __init__(self):
        self.download_folder = os.path.join(os.getcwd(), 'static', 'downloads')
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
    
    def get_available_streams(self, video_id: str) -> Dict:
        """Get video info using yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            url = f"https://www.youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                video_streams = []
                audio_streams = []
                
                for f in info.get('formats', []):
                    if f.get('vcodec') != 'none':
                        video_streams.append({
                            'itag': f.get('format_id'),
                            'resolution': f.get('height'),
                            'mime_type': f.get('ext'),
                            'format_name': f.get('format_note', 'Video')
                        })
                    else:
                        audio_streams.append({
                            'itag': f.get('format_id'),
                            'abr': f.get('abr'),
                            'mime_type': f.get('ext'),
                            'format_name': f.get('format_note', 'Audio')
                        })

                return {
                    'success': True,
                    'title': info.get('title'),
                    'thumbnail': info.get('thumbnail'),
                    'length': info.get('duration'),
                    'author': info.get('uploader'),
                    'video_streams': video_streams[:5],
                    'audio_streams': audio_streams[:5]
                }
        except Exception as e:
            logger.error(f"Error getting info for {video_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def download_video(self, video_id: str, itag: str) -> Dict:
        """Download video using yt-dlp"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            output_template = os.path.join(self.download_folder, '%(title)s-%(id)s.%(ext)s')
            
            ydl_opts = {
                'format': itag,
                'outtmpl': output_template,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                return {
                    'success': True,
                    'title': info.get('title'),
                    'file_path': os.path.relpath(filename, os.getcwd()),
                    'file_size': os.path.getsize(filename) / (1024 * 1024),
                    'mime_type': info.get('ext')
                }
        except Exception as e:
            logger.error(f"Download failed for {video_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def direct_download(self, video_id: str, format_code: str = 'best') -> Dict:
        return self.download_video(video_id, format_code)
