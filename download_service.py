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
                    if not f.get('format_id'):
                        continue

                    vcodec = f.get('vcodec', 'none')
                    acodec = f.get('acodec', 'none')
                    
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else "unknown"

                    # Video streams (including those with and without audio)
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
                    # Pure audio streams
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

                # Sort video by height (highest first)
                video_streams.sort(key=lambda x: int(x['resolution'].replace('p', '')) if x['resolution'].replace('p', '').isdigit() else 0, reverse=True)
                # Sort audio by bitrate (highest first)
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
        """Download video using yt-dlp"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            output_template = os.path.join(self.download_folder, '%(title)s-%(id)s.%(ext)s')
            
            ydl_opts = {
                'format': f"{itag}/best",
                'outtmpl': output_template,
                'quiet': True,
                'merge_output_format': 'mp4',
                'noplaylist': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                if not os.path.exists(filename):
                    # Check for common extensions if the exact filename doesn't exist (due to merging/post-processing)
                    base = filename.rsplit('.', 1)[0]
                    for ext in ['mp4', 'mkv', 'webm']:
                        if os.path.exists(f"{base}.{ext}"):
                            filename = f"{base}.{ext}"
                            break
                
                return {
                    'success': True,
                    'title': info.get('title'),
                    'file_path': os.path.relpath(filename, os.getcwd()),
                    'file_size': round(os.path.getsize(filename) / (1024 * 1024), 2),
                    'mime_type': filename.rsplit('.', 1)[-1]
                }
        except Exception as e:
            logger.error(f"Download failed for {video_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    def direct_download(self, video_id: str, format_code: str = 'best') -> Dict:
        return self.download_video(video_id, format_code)
