"""
Chaturbate Site Implementasyonu - OPTIMIZED
En yüksek kalite + performans optimize
"""

import requests
import dns.resolver
import json
from typing import Dict, Optional

class ChaturbateSite:
    """Chaturbate için optimize edilmiş implementasyon"""
    
    def __init__(self):
        self.site_name = "Chaturbate"
        self.abbreviation = "CB"
        self.base_url = "https://chaturbate.com"
        self.api_url_new = "https://chaturbate.com/api/chatvideocontext/{username}/"
        
        # Headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': 'https://chaturbate.com/'
        }
        
        # DNS resolver
        self._setup_dns_resolver()
        
        # Session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _setup_dns_resolver(self):
        """DNS over HTTPS ayarla"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = ['1.1.1.1', '1.0.0.1']
            
            answers = resolver.resolve('chaturbate.com', 'A')
            self.chaturbate_ip = str(answers[0])
            print(f"[DNS] Chaturbate IP: {self.chaturbate_ip}")
        except:
            print("[DNS] UYARI: DNS cozumu basarisiz")
            self.chaturbate_ip = None
    
    def is_online(self, username: str) -> bool:
        """Yayıncı canlı mı kontrol et"""
        try:
            api_url = self.api_url_new.format(username=username)
            response = self.session.get(api_url, timeout=20, allow_redirects=True, verify=True)
            
            if response.status_code == 200:
                data = response.json()
                room_status = data.get('room_status', '').lower()
                
                if room_status in ['public', 'private', 'group']:
                    hls_source = data.get('hls_source') or data.get('url')
                    return bool(hls_source)
                elif room_status in ['offline', 'away']:
                    return False
                
                hls_source = data.get('hls_source') or data.get('url')
                return bool(hls_source)
            
            return False
                
        except Exception as e:
            print(f"[API] Hata ({username}): {e}")
            return False
    
    def get_stream_url(self, username: str) -> Optional[str]:
        """
        Master playlist URL'ini al
        FFmpeg otomatik en yüksek kaliteyi seçecek
        """
        try:
            api_url = self.api_url_new.format(username=username)
            response = self.session.get(api_url, timeout=20, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"[STREAM URL] API hatasi: {response.status_code}")
                return None
            
            data = response.json()
            hls_source = data.get('hls_source') or data.get('url')
            
            if not hls_source:
                print(f"[STREAM URL] HLS source bulunamadi")
                return None
            
            print(f"[STREAM URL] Master playlist alindi")
            
            # URL düzeltmeleri
            stream_url = hls_source
            cmaf_edge = data.get('cmaf_edge', False)
            
            if cmaf_edge:
                print(f"[STREAM URL] CMAF format")
                stream_url = stream_url.replace('live-edge', 'live-c-fhls')
                stream_url = stream_url.replace('live-hls', 'live-c-fhls')
                stream_url = stream_url.replace('playlist.m3u8', 'playlist_sfm4s.m3u8')
            else:
                print(f"[STREAM URL] Normal format")
                if 'live-edge' in stream_url:
                    stream_url = stream_url.replace('live-edge', 'live-hls')
            
            # Hızlı test (sadece HEAD request)
            if self._quick_test_url(stream_url):
                print(f"[STREAM URL] URL gecerli ✓")
                return stream_url
            else:
                # Alternatif: orijinal dene
                print(f"[STREAM URL] Alternatif deneniyor...")
                if self._quick_test_url(hls_source):
                    print(f"[STREAM URL] Orijinal URL kullaniliyor")
                    return hls_source
                
                # Yine de URL'i döndür, FFmpeg deneyebilir
                print(f"[STREAM URL] Test basarisiz ama URL dondurulecek")
                return stream_url
            
        except Exception as e:
            print(f"[STREAM URL] Exception: {e}")
            return None
    
    def _quick_test_url(self, url: str) -> bool:
        """URL hızlı test (HEAD only)"""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            return response.status_code in [200, 302, 403]
        except:
            return False
    
    def get_thumbnail_url(self, username: str) -> Optional[str]:
        """Yayıncının thumbnail URL'sini al"""
        try:
            # Chaturbate thumbnail formatı
            return f"https://roomimg.stream.highwebmedia.com/ri/{username}.jpg"
        except:
            return None
    
    def get_profile_url(self, username: str) -> str:
        """Yayıncının profil URL'sini al"""
        return f"https://chaturbate.com/{username}/"
    
    def get_stream_info(self, username: str) -> Dict:
        """Stream bilgilerini al"""
        try:
            api_url = self.api_url_new.format(username=username)
            response = self.session.get(api_url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'username': username,
                    'room_status': data.get('room_status', 'unknown'),
                    'is_live': bool(data.get('hls_source') or data.get('url')),
                    'cmaf_edge': data.get('cmaf_edge', False),
                    'thumbnail': self.get_thumbnail_url(username),
                    'profile_url': self.get_profile_url(username)
                }
            return {}
        except:
            return {}


def test_dns():
    """DNS test"""
    print("="*60)
    print("DNS Test")
    print("="*60)
    
    try:
        import socket
        ip = socket.gethostbyname('chaturbate.com')
        print(f"[Sistem DNS] chaturbate.com = {ip}")
    except Exception as e:
        print(f"[Sistem DNS] BASARISIZ: {e}")
    
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['1.1.1.1']
        answers = resolver.resolve('chaturbate.com', 'A')
        print(f"[Cloudflare DNS] chaturbate.com = {answers[0]}")
    except Exception as e:
        print(f"[Cloudflare DNS] BASARISIZ: {e}")
    
    print("\n[HTTP Test]")
    try:
        r = requests.get('https://chaturbate.com', timeout=10)
        print(f"[HTTP Test] BASARILI - Durum: {r.status_code}")
    except Exception as e:
        print(f"[HTTP Test] BASARISIZ: {e}")
    
    print("="*60)


def test_chaturbate(username: str):
    """API test"""
    print(f"\nChaturbate API Test: {username}")
    print("="*60)
    
    cb = ChaturbateSite()
    
    print("\n1. Online kontrolu...")
    is_online = cb.is_online(username)
    print(f"   Sonuc: {'ONLINE' if is_online else 'OFFLINE'}")
    
    if is_online:
        print("\n2. Stream URL...")
        stream_url = cb.get_stream_url(username)
        if stream_url:
            print(f"   URL alindi - FFmpeg en yuksek kaliteyi sececek")
        else:
            print("   URL alinamadi")
        
        print("\n3. Thumbnail URL...")
        thumbnail = cb.get_thumbnail_url(username)
        print(f"   Thumbnail: {thumbnail}")
        
        print("\n4. Profile URL...")
        profile = cb.get_profile_url(username)
        print(f"   Profile: {profile}")
    
    print("="*60)


if __name__ == "__main__":
    print("Chaturbate Implementation - OPTIMIZED")
    print("FFmpeg otomatik en yuksek kaliteyi sececek\n")
    test_dns()