import logging
import os
import yt_dlp
import requests
from pytubefix import YouTube
from typing import Dict

logger = logging.getLogger(__name__)

class DownloadService:
    """Service for downloading YouTube videos using multiple libraries for maximum reliability"""
    
    def __init__(self):
        self.download_folder = os.path.join(os.getcwd(), 'static', 'downloads')
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
        
        self.cookies_path = os.path.join(os.getcwd(), 'cookies.txt')
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
                'remote_components': ['ejs:github'],
                'extractor_args': {'youtube': {'player_client': ['web', 'web_embedded']}},
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
                            'itag': str(f.get('format_id')),
                            'resolution': resolution,
                            'mime_type': f.get('ext') or 'unknown',
                            'size_mb': filesize_mb,
                            'format_name': f"{f.get('format_note') or 'Video'} ({resolution})"
                        })
                    elif acodec != 'none' and vcodec == 'none':
                        abr = f.get('abr')
                        bitrate = f"{int(abr)}kbps" if abr else "unknown"
                        audio_streams.append({
                            'itag': str(f.get('format_id')),
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
            try:
                url = f"https://www.youtube.com/watch?v={video_id}"
                yt = YouTube(url)
                return {
                    'success': True,
                    'title': yt.title,
                    'thumbnail': yt.thumbnail_url,
                    'length': yt.length,
                    'author': yt.author,
                    'video_streams': [{'itag': str(s.itag), 'resolution': s.resolution, 'mime_type': s.mime_type, 'size_mb': 'unknown', 'format_name': f"Video ({s.resolution})"} for s in yt.streams.filter(progressive=True)],
                    'audio_streams': [{'itag': str(s.itag), 'abr': s.abr, 'mime_type': s.mime_type, 'size_mb': 'unknown', 'format_name': f"Audio ({s.abr})"} for s in yt.streams.filter(only_audio=True)]
                }
            except:
                return {'success': False, 'error': str(e)}

    def download_video(self, video_id: str, itag: str) -> Dict:
        """Attempt download using yt-dlp with strict web client strategy"""
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Try yt-dlp first
        result = self._download_with_ytdlp(video_id, itag, url)
        if result['success']:
            return result
            
        # Fallback to pytubefix
        logger.warning(f"yt-dlp failed for {video_id}, trying pytubefix")
        result = self._download_with_pytubefix(video_id, itag, url)
        if result['success']:
            return result
            
        # Emergency last ditch effort
        return self._emergency_fallback_download(video_id)

    def _download_with_ytdlp(self, video_id: str, itag: str, url: str) -> Dict:
        try:
            output_template = os.path.join(self.download_folder, '%(title)s-%(id)s.%(ext)s')
            ydl_opts = {
                'format': f"{itag}/bestvideo+bestaudio/best",
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'cookiefile': self.cookies_path if os.path.exists(self.cookies_path) else None,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'nocheckcertificate': True,
                'ignoreerrors': True,
                'remote_components': ['ejs:github'],
                # Strictly use web clients to bypass current PO Token requirements on mobile clients
                'extractor_args': {'youtube': {'player_client': ['web', 'web_embedded']}},
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info: return {'success': False}
                
                filename = ydl.prepare_filename(info)
                if not os.path.exists(filename):
                    base = filename.rsplit('.', 1)[0]
                    for ext in ['mp4', 'mkv', 'webm', 'm4a']:
                        if os.path.exists(f"{base}.{ext}"):
                            filename = f"{base}.{ext}"
                            break
                
                if os.path.exists(filename):
                    return {
                        'success': True,
                        'title': info.get('title'),
                        'file_path': os.path.relpath(filename, os.getcwd()),
                        'file_size': round(os.path.getsize(filename) / (1024 * 1024), 2),
                        'mime_type': filename.rsplit('.', 1)[-1]
                    }
            return {'success': False}
        except Exception as e:
            logger.error(f"yt-dlp error: {str(e)}")
            return {'success': False}

    def _download_with_pytubefix(self, video_id: str, itag: str, url: str) -> Dict:
        try:
            # Strictly NO OAuth to avoid blocking UI with device codes
            yt = YouTube(url, use_oauth=False)
            stream = None
            if itag and itag.isdigit():
                stream = yt.streams.get_by_id(int(itag))
            if not stream:
                stream = yt.streams.get_highest_resolution()
            
            if not stream: return {'success': False}
            
            target_filename = f"{video_id}_pytube.{stream.subtype}"
            file_path = stream.download(output_path=self.download_folder, filename=target_filename)
            
            return {
                'success': True,
                'title': yt.title,
                'file_path': os.path.relpath(file_path, os.getcwd()),
                'file_size': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                'mime_type': stream.mime_type
            }
        except Exception as e:
            logger.error(f"pytubefix error: {str(e)}")
            return {'success': False}

    def _emergency_fallback_download(self, video_id: str) -> Dict:
        """Final attempt using minimal yt-dlp options and web client"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            output_template = os.path.join(self.download_folder, f"fallback_{video_id}.%(ext)s")
            ydl_opts = {
                'format': 'best', 
                'outtmpl': output_template, 
                'noplaylist': True, 
                'ignoreerrors': True,
                'extractor_args': {'youtube': {'player_client': ['web']}},
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info: return {'success': False, 'error': "All strategies failed"}
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    return {
                        'success': True,
                        'title': info.get('title', 'Video'),
                        'file_path': os.path.relpath(filename, os.getcwd()),
                        'file_size': round(os.path.getsize(filename) / (1024 * 1024), 2),
                        'mime_type': filename.rsplit('.', 1)[-1]
                    }
            return {'success': False, 'error': "All strategies failed"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def direct_download(self, video_id: str, format_code: str = 'best') -> Dict:
        return self.download_video(video_id, format_code)
