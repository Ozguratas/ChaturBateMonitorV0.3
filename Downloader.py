#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Downloader.py - AUTO START VERSION + SNAPSHOT SUPPORT
Program açılır açılmaz tüm yayıncılar otomatik izlenmeye başlar
FFmpeg ile yayından snapshot alınır

⚠️ UYARI: Sadece eğitim amaçlıdır!
"""

import sys
import os

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

import json
import threading
import time
import subprocess
import signal
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    from chaturbate_implementation import ChaturbateSite
except ImportError:
    print("HATA: chaturbate_implementation.py dosyası bulunamadı!")
    sys.exit(1)


# ============================================================================
# Config
# ============================================================================

class Config:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_data = self.load()
    
    def load(self) -> dict:
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'streamers': []}
        return {'streamers': []}
    
    def save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Config save error: {e}")
    
    def add_streamer(self, username: str, site: str):
        streamer = {'username': username, 'site': site}
        if streamer not in self.config_data['streamers']:
            self.config_data['streamers'].append(streamer)
            self.save()
            return True
        return False
    
    def remove_streamer(self, username: str, site: str = None):
        streamers = self.config_data['streamers']
        if site:
            streamer = {'username': username, 'site': site}
            if streamer in streamers:
                streamers.remove(streamer)
                self.save()
                return True
        else:
            self.config_data['streamers'] = [s for s in streamers if s['username'] != username]
            self.save()
            return True
        return False
    
    def get_streamers(self) -> List[dict]:
        return self.config_data['streamers']


# ============================================================================
# Recorder - OPTIMIZED + SNAPSHOT SUPPORT
# ============================================================================

class Recorder:
    """FFmpeg ile kayıt + snapshot - EN YÜKSEK KALİTE"""
    
    def __init__(self, output_dir: str = "recordings", static_dir: str = "static/users"):
        self.output_dir = output_dir
        self.static_dir = static_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        Path(static_dir).mkdir(parents=True, exist_ok=True)
        print(f"[RECORDER] Kayit klasoru: {os.path.abspath(output_dir)}")
        print(f"[RECORDER] Snapshot klasoru: {os.path.abspath(static_dir)}")
    
    def capture_snapshot(self, stream_url: str, username: str) -> bool:
        """
        Yayından bir frame yakalayıp static/users/{username}.jpg olarak kaydet
        """
        try:
            snapshot_path = os.path.join(self.static_dir, f"{username}.jpg")
            
            # Eğer zaten varsa ve 1 saatten yeni ise skip
            if os.path.exists(snapshot_path):
                file_age = time.time() - os.path.getmtime(snapshot_path)
                if file_age < 3600:  # 1 saat
                    print(f"[SNAPSHOT] {username} - Mevcut snapshot yeni, atlaniyor")
                    return True
            
            print(f"[SNAPSHOT] {username} - Yayin goruntusü yakalaniyor...")
            
            # FFmpeg snapshot komutu
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'error',
                '-i', stream_url,
                '-vframes', '1',           # Sadece 1 frame
                '-q:v', '2',               # Yüksek kalite
                '-vf', 'scale=400:-1',     # 400px genişlik, aspect ratio koru
                '-y',                       # Üzerine yaz
                snapshot_path
            ]
            
            # Timeout ile çalıştır (max 10 saniye)
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10
            )
            
            if process.returncode == 0 and os.path.exists(snapshot_path):
                size = os.path.getsize(snapshot_path)
                print(f"[SNAPSHOT] ✓ {username} - {size} bytes kaydedildi")
                return True
            else:
                print(f"[SNAPSHOT] ✗ {username} - Yakalama basarisiz")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[SNAPSHOT] ✗ {username} - Timeout (10 saniye)")
            return False
        except Exception as e:
            print(f"[SNAPSHOT] ✗ {username} - Hata: {e}")
            return False
    
    def start_recording(self, stream_url: str, username: str, site: str) -> Optional[subprocess.Popen]:
        """
        Kaydı başlat - EN YÜKSEK KALİTE
        FFmpeg master playlist'ten otomatik en yüksek kaliteyi seçer
        Kayıtlar kullanıcı adına göre klasörlere ayrılır
        """
        try:
            # Kullanıcı için klasör oluştur
            user_dir = os.path.join(self.output_dir, username)
            Path(user_dir).mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{site}_{username}_{timestamp}.mp4"
            filepath = os.path.abspath(os.path.join(user_dir, filename))
            
            print(f"\n{'='*70}")
            print(f"[KAYIT BASLATIILIYOR]")
            print(f"  Kullanici: {username}")
            print(f"  Klasor: {user_dir}")
            print(f"  Dosya: {filename}")
            print(f"  Kalite: EN YUKSEK (FFmpeg otomatik)")
            print(f"{'='*70}\n")
            
            # Snapshot al (non-blocking thread)
            threading.Thread(
                target=self.capture_snapshot,
                args=(stream_url, username),
                daemon=True
            ).start()
            
            # FFmpeg komutu - OPTIMIZE EDİLMİŞ
            cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'warning',
                
                # HLS optimizasyonları
                '-reconnect', '1',
                '-reconnect_streamed', '1',
                '-reconnect_delay_max', '5',
                '-timeout', '10000000',
                
                '-i', stream_url,
                
                # Codec ayarları
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-bsf:a', 'aac_adtstoasc',
                
                # Output
                '-movflags', '+faststart',
                '-y',
                filepath
            ]
            
            print(f"[FFmpeg] Process baslatiliyor...")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            print(f"[FFmpeg] PID: {process.pid}")
            
            # Kısa kontrol
            time.sleep(3)
            
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                print(f"\n[FFmpeg] HATA - Process durdu!")
                print(f"[FFmpeg] Return code: {process.returncode}")
                if stderr:
                    print(f"[FFmpeg] Hata:\n{stderr.decode('utf-8', errors='ignore')}")
                return None
            
            print(f"[FFmpeg] Kayit basarili! EN YUKSEK kalite secildi ✓")
            
            # Dosya kontrolü
            time.sleep(2)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"[Dosya] {size} bytes yazildi")
            
            return process
            
        except FileNotFoundError:
            print("\n[HATA] FFmpeg bulunamadi!")
            print("https://ffmpeg.org/download.html adresinden yukleyin")
            return None
        except Exception as e:
            print(f"\n[HATA] {e}")
            return None
    
    def stop_recording(self, process: subprocess.Popen) -> bool:
        """Kaydı durdur"""
        try:
            if process and process.poll() is None:
                print(f"\n[KAYIT DURDURULUYOR] PID: {process.pid}")
                
                process.stdin.write(b'q')
                process.stdin.flush()
                
                try:
                    process.wait(timeout=10)
                    print(f"[KAYIT TAMAMLANDI] ✓")
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    print(f"[KAYIT TAMAMLANDI] (zorla) ✓")
                
                return True
            return False
        except Exception as e:
            print(f"[HATA] Stop error: {e}")
            return False


# ============================================================================
# Streamer & Monitor
# ============================================================================

class Streamer:
    def __init__(self, username: str, site_obj):
        self.username = username
        self.site = site_obj
        self.is_monitoring = False
        self.is_recording = False
        self.last_check = None
        self.recording_process = None
        self.monitor_thread = None
        self.should_stop = False
        self.is_online = False
        self.check_count = 0
        self.recording_start_time = None


class StreamMonitor:
    def __init__(self, check_interval: int = 60):
        self.streamers: Dict[str, Streamer] = {}
        self.recorder = Recorder()
        self.check_interval = check_interval
        self.running = True
        self.sites = {'CB': ChaturbateSite()}
    
    def get_site(self, abbreviation: str):
        return self.sites.get(abbreviation.upper())
    
    def add_streamer(self, username: str, site_abbr: str) -> bool:
        site = self.get_site(site_abbr)
        if not site:
            print(f"Hata: '{site_abbr}' sitesi desteklenmiyor")
            return False
        
        key = f"{username}@{site_abbr}"
        if key in self.streamers:
            print(f"'{username}' zaten listede")
            return False
        
        streamer = Streamer(username, site)
        self.streamers[key] = streamer
        print(f"OK Eklendi: {username}@{site_abbr}")
        return True
    
    def remove_streamer(self, username: str, site_abbr: str = None) -> bool:
        if site_abbr:
            key = f"{username}@{site_abbr.upper()}"
            if key in self.streamers:
                self.stop_monitoring(username, site_abbr)
                del self.streamers[key]
                print(f"OK Cikarildi: {key}")
                return True
        else:
            removed = False
            for key in list(self.streamers.keys()):
                if key.startswith(username + "@"):
                    site = key.split("@")[1]
                    self.stop_monitoring(username, site)
                    del self.streamers[key]
                    removed = True
            return removed
        return False
    
    def start_monitoring(self, username: str, site_abbr: str = None):
        for key, streamer in self.streamers.items():
            if streamer.username == username:
                if site_abbr and streamer.site.abbreviation.upper() != site_abbr.upper():
                    continue
                
                if not streamer.is_monitoring:
                    streamer.is_monitoring = True
                    streamer.should_stop = False
                    
                    thread = threading.Thread(
                        target=self._monitor_loop,
                        args=(streamer,),
                        daemon=True
                    )
                    thread.start()
                    streamer.monitor_thread = thread
                    print(f"START Izleme baslatildi: {key}")
    
    def stop_monitoring(self, username: str, site_abbr: str = None):
        for key, streamer in self.streamers.items():
            if streamer.username == username:
                if site_abbr and streamer.site.abbreviation.upper() != site_abbr.upper():
                    continue
                
                streamer.should_stop = True
                streamer.is_monitoring = False
                
                if streamer.is_recording:
                    self.recorder.stop_recording(streamer.recording_process)
                    streamer.is_recording = False
                    streamer.recording_start_time = None
                
                print(f"PAUSE Izleme durduruldu: {key}")
    
    def start_all(self):
        """TÜM yayıncılar için izlemeyi başlat"""
        count = 0
        for streamer in self.streamers.values():
            if not streamer.is_monitoring:
                self.start_monitoring(streamer.username, streamer.site.abbreviation)
                count += 1
        return count
    
    def stop_all(self):
        for streamer in self.streamers.values():
            if streamer.is_monitoring:
                self.stop_monitoring(streamer.username, streamer.site.abbreviation)
    
    def _monitor_loop(self, streamer: Streamer):
        """Monitor loop"""
        while not streamer.should_stop and self.running:
            try:
                streamer.last_check = datetime.now()
                streamer.check_count += 1
                
                is_online = streamer.site.is_online(streamer.username)
                streamer.is_online = is_online
                
                if is_online and not streamer.is_recording:
                    print(f"\n[MONITOR] {streamer.username} ONLINE")
                    stream_url = streamer.site.get_stream_url(streamer.username)
                    
                    if stream_url:
                        process = self.recorder.start_recording(
                            stream_url,
                            streamer.username,
                            streamer.site.abbreviation
                        )
                        if process:
                            streamer.recording_process = process
                            streamer.is_recording = True
                            streamer.recording_start_time = datetime.now()
                
                elif not is_online and streamer.is_recording:
                    print(f"\n[MONITOR] {streamer.username} OFFLINE")
                    self.recorder.stop_recording(streamer.recording_process)
                    streamer.is_recording = False
                    streamer.recording_start_time = None
                
            except Exception as e:
                print(f"[MONITOR] Error ({streamer.username}): {e}")
            
            time.sleep(self.check_interval)
    
    def print_status(self):
        """Detaylı görsel durum tablosu"""
        if not self.streamers:
            print("\nHenuz yayinci eklenmedi.\n")
            return
        
        print("\n" + "="*100)
        print(f"{'Kullanici':<20} {'Durum':<15} {'Kayit':<20} {'Sure':<12} {'Kontrol':<8} {'Thread':<10}")
        print("="*100)
        
        for streamer in self.streamers.values():
            # Durum
            if streamer.is_online:
                status = "🟢 online"
            else:
                status = "⚫ offline"
            
            # Kayıt durumu
            if streamer.is_recording:
                recording = "🔴 Kaydediyor"
            else:
                recording = "⏸️  Beklemede"
            
            # Kayıt süresi
            if streamer.is_recording and streamer.recording_start_time:
                duration = datetime.now() - streamer.recording_start_time
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                seconds = int(duration.total_seconds() % 60)
                
                if hours > 0:
                    duration_str = f"{hours}s {minutes:02d}d {seconds:02d}sn"
                else:
                    duration_str = f"{minutes:02d}d {seconds:02d}sn"
            else:
                duration_str = "-"
            
            # Thread durumu
            thread_status = "✅ ▶️" if streamer.is_monitoring else "❌ ⏸️"
            
            # Kontrol sayısı
            check_count = str(streamer.check_count)
            
            print(
                f"{streamer.username:<20} "
                f"{status:<15} "
                f"{recording:<20} "
                f"{duration_str:<12} "
                f"{check_count:<8} "
                f"{thread_status:<10}"
            )
        
        print("="*100 + "\n")
    
    def shutdown(self):
        print("\nKapatiliyor...")
        self.running = False
        self.stop_all()
        time.sleep(1)


# ============================================================================
# Console
# ============================================================================

def print_banner():
    print("""
================================================================
     Stream Monitor - AUTO START VERSION + SNAPSHOT
                                                          
  Program acilir acilmaz TUM yayincilar otomatik izlenir!
  FFmpeg otomatik en yuksek kaliteyi sececek
  Yayindan snapshot alinacak (static/users/)
================================================================
""")


def print_help():
    print("""
Komutlar:
  add <username> CB     - Yayinci ekle (otomatik baslar)
  remove <username> CB  - Yayinci cikar
  start <username> CB   - Izlemeyi baslat (zaten otomatik)
  start *               - Tumunu baslat (zaten otomatik)
  stop <username> CB    - Izlemeyi durdur
  stop *                - Tumunu durdur
  status                - Durum goster
  files                 - Kayitlari listele
  help                  - Bu mesaj
  quit                  - Cikis
""")


def main():
    print_banner()
    
    # Klasör kontrolü
    Path("static/users").mkdir(parents=True, exist_ok=True)
    Path("static/logos").mkdir(parents=True, exist_ok=True)
    
    config = Config()
    monitor = StreamMonitor(check_interval=60)
    
    print("Config dosyasindan yayincilar yukleniyor...\n")
    
    # Config'den yükle
    loaded_count = 0
    for s in config.get_streamers():
        if monitor.add_streamer(s['username'], s['site']):
            loaded_count += 1
    
    print(f"OK {loaded_count} yayinci yuklendi")
    
    # ★★★ OTOMATIK BAŞLAT ★★★
    if loaded_count > 0:
        print("\n" + "="*70)
        print("OTOMATIK IZLEME BASLATILIYOR...")
        print("="*70 + "\n")
        
        started_count = monitor.start_all()
        
        print(f"\n✓ {started_count} yayinci icin izleme AKTIF!")
        print("Yayin baslayinca otomatik kayit yapilacak.")
        print("Yayin goruntuleri static/users/ klasorune kaydedilecek.")
        
        # İlk kontroller için bekle
        print("\nIlk kontroller yapiliyor (5 saniye)...")
        time.sleep(5)
        
        # İlk durumu göster
        print("\n>>> ILK DURUM <<<")
        monitor.print_status()
    else:
        print("\n! Henuz yayinci yok. Eklemek icin: add <username> CB\n")
    
    # Signal handler
    def signal_handler(sig, frame):
        print("\n\nCtrl+C")
        monitor.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Ana loop
    while True:
        try:
            cmd_input = input("(monitor) ").strip()
            if not cmd_input:
                continue
            
            parts = cmd_input.split()
            cmd = parts[0].lower()
            
            if cmd in ['quit', 'exit']:
                monitor.shutdown()
                config.save()
                print("Gule gule!")
                break
            
            elif cmd == 'help':
                print_help()
            
            elif cmd == 'add':
                if len(parts) < 3:
                    print("Kullanim: add <username> CB")
                    continue
                username, site = parts[1], parts[2].upper()
                if monitor.add_streamer(username, site):
                    config.add_streamer(username, site)
                    # Hemen başlat
                    monitor.start_monitoring(username, site)
            
            elif cmd == 'remove':
                if len(parts) < 2:
                    print("Kullanim: remove <username> [CB]")
                    continue
                username = parts[1]
                site = parts[2].upper() if len(parts) > 2 else None
                if monitor.remove_streamer(username, site):
                    config.remove_streamer(username, site)
            
            elif cmd == 'start':
                if len(parts) < 2:
                    print("Kullanim: start <username> [CB]  veya  start *")
                    continue
                if parts[1] == '*':
                    count = monitor.start_all()
                    print(f"OK {count} yayinci baslatildi")
                else:
                    username = parts[1]
                    site = parts[2].upper() if len(parts) > 2 else None
                    monitor.start_monitoring(username, site)
            
            elif cmd == 'stop':
                if len(parts) < 2:
                    print("Kullanim: stop <username> [CB]  veya  stop *")
                    continue
                if parts[1] == '*':
                    monitor.stop_all()
                else:
                    username = parts[1]
                    site = parts[2].upper() if len(parts) > 2 else None
                    monitor.stop_monitoring(username, site)
            
            elif cmd == 'status':
                monitor.print_status()
            
            elif cmd == 'files':
                rec_dir = "recordings"
                if os.path.exists(rec_dir):
                    files = sorted([f for f in os.listdir(rec_dir) if f.endswith('.mp4')])
                    if files:
                        print(f"\nKayitlar ({len(files)} dosya):")
                        print("="*70)
                        total_size = 0
                        for f in files:
                            fpath = os.path.join(rec_dir, f)
                            size = os.path.getsize(fpath)
                            size_mb = size / (1024 * 1024)
                            total_size += size
                            print(f"  {f:<50} {size_mb:>8.2f} MB")
                        print("="*70)
                        print(f"  Toplam: {total_size/(1024*1024):.2f} MB\n")
                    else:
                        print("\nHenuz kayit yok.\n")
                else:
                    print("\nKayit klasoru yok.\n")
            
            else:
                print(f"Bilinmeyen komut: {cmd}")
        
        except EOFError:
            monitor.shutdown()
            break
        except Exception as e:
            print(f"Hata: {e}")


if __name__ == "__main__":
    main()