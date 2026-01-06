import logging
import os
import yt_dlp
import requests
from typing import Dict

logger = logging.getLogger(__name__)

class DownloadService:
    """Service for downloading YouTube videos using yt-dlp with maximum bypass capabilities"""
    
    def __init__(self):
        self.download_folder = os.path.join(os.getcwd(), 'static', 'downloads')
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
        
        self.cookies_path = os.path.join(os.getcwd(), 'cookies.txt')
        # Create an empty cookies file if it doesn't exist
        if not os.path.exists(self.cookies_path):
            with open(self.cookies_path, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
    
    def get_available_streams(self, video_id: str) -> Dict:
        """Get video info using yt-dlp with bypass settings"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'cookiefile': self.cookies_path if os.path.exists(self.cookies_path) else None,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'nocheckcertificate': True,
            }
            url = f"https://www.youtube.com/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                video_streams = []
                audio_streams = []
                
                for f in info.get('formats', []):
                    if not f.get('format_id'): continue

                    vcodec = f.get('vcodec', 'none')
                    acodec = f.get('acodec', 'none')
                    
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else "unknown"

                    if vcodec != 'none':
                        height = f.get('height')
                        resolution = f"{height}p" if height else "unknown"
                        video_streams.append({
                            'itag': f.get('format_id'),
                            'resolution': resolution,
                            'mime_type': f.get('ext') or 'unknown',
                            'size_mb': filesize_mb,
                            'format_name': f"{f.get('format_note') or 'Video'} ({resolution})"
                        })
                    elif acodec != 'none' and vcodec == 'none':
                        abr = f.get('abr')
                        bitrate = f"{int(abr)}kbps" if abr else "unknown"
                        audio_streams.append({
                            'itag': f.get('format_id'),
                            'abr': bitrate,
                            'mime_type': f.get('ext') or 'unknown',
                            'size_mb': filesize_mb,
                            'format_name': f"{f.get('format_note') or 'Audio'} ({bitrate})"
                        })

                video_streams.sort(key=lambda x: int(x['resolution'].replace('p', '')) if x['resolution'].replace('p', '').isdigit() else 0, reverse=True)
                audio_streams.sort(key=lambda x: int(x['abr'].replace('kbps', '')) if x['abr'].replace('kbps', '').isdigit() else 0, reverse=True)

                return {
                    'success': True,
                    'title': info.get('title'),
                    'thumbnail': info.get('thumbnail'),
                    'length': info.get('duration'),
                    'author': info.get('uploader'),
                    'video_streams': video_streams[:15],
                    'audio_streams': audio_streams[:15]
                }
        except Exception as e:
            logger.error(f"Error getting info for {video_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def download_video(self, video_id: str, itag: str) -> Dict:
        """Force download using multiple bypass strategies"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            output_template = os.path.join(self.download_folder, '%(title)s-%(id)s.%(ext)s')
            
            # Primary strategy: Specific format with fallback
            ydl_opts = {
                'format': f"{itag}/bestvideo+bestaudio/best",
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'cookiefile': self.cookies_path if os.path.exists(self.cookies_path) else None,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'external_downloader': 'aria2c' if os.path.exists('/usr/bin/aria2c') else None,
                'http_headers': {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                }
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise Exception("Failed to extract info or download")
                
                filename = ydl.prepare_filename(info)
                
                # Check for processed files (merging often changes extensions)
                if not os.path.exists(filename):
                    base = filename.rsplit('.', 1)[0]
                    for ext in ['mp4', 'mkv', 'webm', 'm4a']:
                        if os.path.exists(f"{base}.{ext}"):
                            filename = f"{base}.{ext}"
                            break
                
                if not os.path.exists(filename):
                    # Fallback to searching for the file with the video ID in the name
                    files = [f for f in os.listdir(self.download_folder) if video_id in f]
                    if files:
                        filename = os.path.join(self.download_folder, files[0])
                    else:
                        raise Exception("Downloaded file not found on disk")
                
                return {
                    'success': True,
                    'title': info.get('title'),
                    'file_path': os.path.relpath(filename, os.getcwd()),
                    'file_size': round(os.path.getsize(filename) / (1024 * 1024), 2),
                    'mime_type': filename.rsplit('.', 1)[-1]
                }
        except Exception as e:
            logger.error(f"Download failed for {video_id}: {str(e)}")
            # Last ditch effort: Try downloading just the best combined format with no extra bells and whistles
            return self._emergency_fallback_download(video_id)

    def _emergency_fallback_download(self, video_id: str) -> Dict:
        """Final attempt to download using minimal options"""
        try:
            logger.info(f"Running emergency fallback for {video_id}")
            url = f"https://www.youtube.com/watch?v={video_id}"
            output_template = os.path.join(self.download_folder, f"fallback_{video_id}.%(ext)s")
            
            ydl_opts = {
                'format': 'best',
                'outtmpl': output_template,
                'noplaylist': True,
                'ignoreerrors': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    return {
                        'success': True,
                        'title': info.get('title', 'Video'),
                        'file_path': os.path.relpath(filename, os.getcwd()),
                        'file_size': round(os.path.getsize(filename) / (1024 * 1024), 2),
                        'mime_type': filename.rsplit('.', 1)[-1]
                    }
            return {'success': False, 'error': "All download strategies failed"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def direct_download(self, video_id: str, format_code: str = 'best') -> Dict:
        return self.download_video(video_id, format_code)
