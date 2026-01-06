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
                    # Filter out formats that don't have basic required info
                    if not f.get('format_id'):
                        continue

                    # Determine if it's video or audio
                    vcodec = f.get('vcodec', 'none')
                    acodec = f.get('acodec', 'none')
                    
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else "unknown"

                    if vcodec != 'none':
                        resolution = f.get('height') or f.get('resolution') or 'unknown'
                        video_streams.append({
                            'itag': f.get('format_id'),
                            'resolution': f.get('height') or resolution,
                            'mime_type': f.get('ext') or 'unknown',
                            'size_mb': filesize_mb,
                            'format_name': f"{f.get('format_note', 'Video')} ({resolution}p)"
                        })
                    elif acodec != 'none':
                        audio_streams.append({
                            'itag': f.get('format_id'),
                            'abr': f.get('abr') or 'unknown',
                            'mime_type': f.get('ext') or 'unknown',
                            'size_mb': filesize_mb,
                            'format_name': f"{f.get('format_note', 'Audio')} ({f.get('abr', 'unknown')}kbps)"
                        })

                # Sort streams by resolution/bitrate
                video_streams.sort(key=lambda x: int(x['resolution']) if isinstance(x['resolution'], (int, str)) and str(x['resolution']).isdigit() else 0, reverse=True)
                audio_streams.sort(key=lambda x: float(x['abr']) if isinstance(x['abr'], (int, float, str)) and str(x['abr']).replace('.','',1).isdigit() else 0, reverse=True)

                return {
                    'success': True,
                    'title': info.get('title'),
                    'thumbnail': info.get('thumbnail'),
                    'length': info.get('duration'),
                    'author': info.get('uploader'),
                    'video_streams': video_streams[:10],
                    'audio_streams': audio_streams[:10]
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
                'format': f"{itag}+bestaudio/best",
                'outtmpl': output_template,
                'quiet': True,
                'merge_output_format': 'mp4'
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # If we merged formats, the extension might have changed to mp4
                if not os.path.exists(filename) and os.path.exists(filename.rsplit('.', 1)[0] + '.mp4'):
                    filename = filename.rsplit('.', 1)[0] + '.mp4'
                
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
