#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_static_folders.py - Static klasör yapısını oluştur
"""

import os
from pathlib import Path

def create_folder_structure():
    """Static klasör yapısını oluştur"""
    
    folders = [
        'static',
        'static/logos',
        'static/users',
        'recordings'
    ]
    
    print("="*60)
    print("KLASÖR YAPISI OLUŞTURULUYOR")
    print("="*60)
    
    for folder in folders:
        path = Path(folder)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Oluşturuldu: {folder}")
        else:
            print(f"✓ Mevcut: {folder}")
    
    print("="*60)
    print("\nKLASÖR YAPISI:")
    print("""
    project/
    ├── static/
    │   ├── logos/
    │   │   └── chaturbate.png  ← Site logosunu buraya koy
    │   └── users/
    │       └── {username}.jpg  ← FFmpeg snapshot'lar (otomatik)
    ├── recordings/
    │   └── {username}/
    │       └── *.mp4
    └── ...
    """)
    print("="*60)
    print("\n📝 ÖNEMLİ:")
    print("   static/logos/chaturbate.png dosyasını manuel olarak ekleyin!")
    print("   Kullanıcı snapshot'ları otomatik oluşturulacak.\n")
    print("="*60)


if __name__ == "__main__":
    create_folder_structure()