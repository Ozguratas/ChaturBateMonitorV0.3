#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_interface.py - Flask Web Interface
Modern web arayüzü + Tüm Özellikler
"""

import os
import sys
import json
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, send_file, Response
from werkzeug.utils import secure_filename

# Mevcut modülleri import et
from Downloader import StreamMonitor, Config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['RECORDINGS_DIR'] = 'recordings'
app.config['STATIC_DIR'] = 'static'

# Global monitor instance
monitor = None
config = None

# Static klasörleri oluştur
Path("static/users").mkdir(parents=True, exist_ok=True)
Path("static/logos").mkdir(parents=True, exist_ok=True)

# ============================================================================
# HTML Template - FULL FEATURED
# ============================================================================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stream Monitor Pro</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #0a0e27;
            min-height: 100vh;
            padding: 30px;
            color: #fff;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.3) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.3) 0px, transparent 50%);
        }
        
        .container { max-width: 1800px; margin: 0 auto; }
        
        .header {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }
        
        .header h1 {
            font-size: 3em;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .header p { color: rgba(255, 255, 255, 0.6); font-size: 1.2em; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            position: relative;
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            transition: all 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 32px 0 rgba(99, 102, 241, 0.4);
        }
        
        .stat-value {
            font-size: 3.5em;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .stat-label { color: rgba(255, 255, 255, 0.6); font-size: 1.1em; font-weight: 500; }
        
        /* NOTIFICATION BADGE */
        .stat-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            color: white;
            font-size: 0.8em;
            font-weight: 700;
            padding: 4px 8px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(235, 51, 73, 0.5);
            animation: bounce 0.5s ease;
        }
        
        @keyframes bounce {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }
        
        .section {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 30px;
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #fff;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .tab {
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1.1em;
            color: rgba(255, 255, 255, 0.6);
            transition: all 0.3s;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom: 3px solid #667eea;
            margin-bottom: -2px;
        }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* SEARCH BAR */
        .search-container {
            position: relative;
            margin-bottom: 20px;
        }
        
        .search-input {
            width: 100%;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px 20px 15px 50px;
            font-size: 1em;
            color: #fff;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
            background: rgba(255, 255, 255, 0.08);
        }
        
        .search-input::placeholder { color: rgba(255, 255, 255, 0.4); }
        
        .search-icon {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 1.2em;
            color: rgba(255, 255, 255, 0.4);
        }
        
        /* QUICK ACTIONS */
        .quick-actions {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .quick-action-btn {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: white;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Inter', sans-serif;
            font-weight: 600;
            font-size: 0.95em;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .quick-action-btn:hover {
            background: rgba(255, 255, 255, 0.1);
            transform: translateY(-2px);
            border-color: #667eea;
        }
        
        /* ADD STREAMER FORM */
        .add-streamer-form {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .form-input {
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px 20px;
            font-size: 1em;
            color: #fff;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #667eea;
            background: rgba(255, 255, 255, 0.08);
        }
        
        .form-input::placeholder { color: rgba(255, 255, 255, 0.4); }
        
        /* VIEW TOGGLE */
        .view-controls {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .view-btn {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.6);
            cursor: pointer;
            transition: all 0.3s;
            font-size: 1.2em;
        }
        
        .view-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
            color: white;
        }
        
        .view-btn:hover {
            transform: scale(1.05);
        }
        
        /* EMPTY STATE */
        .empty-state {
            text-align: center;
            padding: 80px 40px;
            color: rgba(255, 255, 255, 0.6);
        }
        
        .empty-icon {
            font-size: 80px;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .empty-state h3 {
            font-size: 1.8em;
            color: white;
            margin-bottom: 10px;
        }
        
        .empty-state p {
            font-size: 1.1em;
        }
        
        /* PROFILE CARDS (GRID VIEW) */
        .streamer-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 30px;
        }
        
        .streamer-grid.list-view {
            grid-template-columns: 1fr;
            gap: 15px;
        }
        
        .profile-card {
            position: relative;
            width: 100%;
            height: 450px;
            border-radius: 20px;
            box-shadow: 0 10px 25px 5px rgba(0, 0, 0, 0.3);
            background: rgba(21, 21, 21, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
            animation: cardAppear 0.5s ease-out;
            transition: all 0.3s;
        }
        
        .profile-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 40px 10px rgba(102, 126, 234, 0.3);
        }
        
        .profile-card.recording {
            border: 2px solid #dc3545;
            box-shadow: 0 10px 25px 5px rgba(220, 53, 69, 0.4);
        }
        
        /* LIST VIEW */
        .profile-card.list-mode {
            height: 120px;
            display: flex;
            flex-direction: row;
        }
        
        .profile-card.list-mode .card-top {
            position: relative;
            width: 120px;
            height: 100%;
        }
        
        .profile-card.list-mode .avatar-holder {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
        }
        
        .profile-card.list-mode .avatar-holder .status-badge {
            width: 25px;
            height: 25px;
            font-size: 14px;
            bottom: 2px;
            right: 2px;
            border: 2px solid rgba(21, 21, 21, 0.95);
        }
        
        .profile-card.list-mode .card-content {
            flex: 1;
            display: flex;
            align-items: center;
            padding: 20px;
            gap: 30px;
        }
        
        .profile-card.list-mode .card-name {
            position: relative;
            top: auto;
            left: auto;
            text-align: left;
            flex: 1;
        }
        
        .profile-card.list-mode .card-stats {
            position: relative;
            top: auto;
            display: flex;
            gap: 30px;
            padding: 0;
        }
        
        .profile-card.list-mode .card-actions {
            position: relative;
            bottom: auto;
            left: auto;
            right: auto;
            display: flex;
            gap: 10px;
        }
        
        .profile-card.list-mode .site-logo {
            top: 5px;
            right: 5px;
            width: 50px;
            height: 50px;
        }
        
        /* CARD DESIGN */
        .card-top {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 100px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .card-top.recording {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            animation: pulse 2s infinite;
        }
        
        .site-logo {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 90px;
            height: 90px;
            background: transparent;
            border-radius: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.5));
            z-index: 10;
        }
        
        .site-logo img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }
        
        .avatar-holder {
            position: absolute;
            top: 50px;
            left: 50%;
            transform: translateX(-50%);
            width: 120px;
            height: 120px;
            border-radius: 50%;
            box-shadow: 0 0 0 5px rgba(21, 21, 21, 0.95),
                        0 0 20px rgba(102, 126, 234, 0.5);
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: visible;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .avatar-holder img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 50%;
        }
        
        .avatar-holder .status-badge {
            position: absolute;
            bottom: 5px;
            right: 5px;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            background: rgba(21, 21, 21, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            border: 3px solid rgba(21, 21, 21, 0.95);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
            z-index: 10;
        }
        
        .avatar-holder .status-icon-center {
            font-size: 60px;
        }
        
        .card-name {
            position: absolute;
            top: 185px;
            left: 0;
            right: 0;
            text-align: center;
        }
        
        .card-name h3 {
            color: white;
            font-weight: 700;
            font-size: 20px;
            margin-bottom: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .card-name h3:hover {
            color: #667eea;
            text-decoration: underline;
        }
        
        .card-name .status {
            color: rgba(255, 255, 255, 0.6);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.3s ease;
        }
        
        .card-stats {
            position: absolute;
            top: 240px;
            left: 0;
            right: 0;
            display: flex;
            justify-content: space-around;
            padding: 0 20px;
        }
        
        .stat-item { text-align: center; }
        
        .stat-item h6 {
            color: #667eea;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 5px;
            font-weight: 700;
        }
        
        .stat-item p {
            color: white;
            font-size: 18px;
            font-weight: 700;
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .card-actions {
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }
        
        /* BUTTONS */
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Inter', sans-serif;
            white-space: nowrap;
            flex: 1;
        }
        
        .btn:hover { transform: scale(1.05); }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
            color: white;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
            box-shadow: 0 4px 15px 0 rgba(56, 239, 125, 0.5);
        }
        
        .btn-videos {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }
        
        /* TOAST NOTIFICATIONS */
        .toast-container {
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 3000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .toast {
            padding: 16px 24px;
            border-radius: 12px;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideInRight 0.3s ease;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            min-width: 300px;
        }
        
        .toast.success {
            background: rgba(56, 239, 125, 0.15);
            border: 1px solid #38ef7d;
            color: #38ef7d;
        }
        
        .toast.error {
            background: rgba(235, 51, 73, 0.15);
            border: 1px solid #eb3349;
            color: #eb3349;
        }
        
        .toast.info {
            background: rgba(102, 126, 234, 0.15);
            border: 1px solid #667eea;
            color: #667eea;
        }
        
        .toast-icon {
            font-size: 1.5em;
        }
        
        .toast-close {
            margin-left: auto;
            cursor: pointer;
            opacity: 0.6;
            transition: opacity 0.3s;
        }
        
        .toast-close:hover {
            opacity: 1;
        }
        
        /* NETWORK STATUS */
        .network-status {
            position: fixed;
            bottom: 70px;
            right: 20px;
            padding: 12px 20px;
            background: rgba(21, 21, 21, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.9em;
            z-index: 1000;
            backdrop-filter: blur(10px);
            transition: all 0.3s;
        }
        
        .network-status.online {
            border-color: #38ef7d;
        }
        
        .network-status.offline {
            border-color: #eb3349;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .network-status.online .status-dot {
            background: #38ef7d;
            box-shadow: 0 0 10px #38ef7d;
        }
        
        .network-status.offline .status-dot {
            background: #eb3349;
            box-shadow: 0 0 10px #eb3349;
        }
        
        /* KEYBOARD HINT */
        .keyboard-hint {
            position: fixed;
            bottom: 20px;
            left: 20px;
            padding: 12px 20px;
            background: rgba(21, 21, 21, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            font-size: 0.85em;
            color: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .keyboard-hint kbd {
            background: rgba(255, 255, 255, 0.1);
            padding: 4px 8px;
            border-radius: 4px;
            font-family: monospace;
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* LOADING OVERLAY */
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(10, 14, 39, 0.8);
            backdrop-filter: blur(5px);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 2000;
        }
        
        .loading-overlay.active {
            display: flex;
        }
        
        .loading-spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(255, 255, 255, 0.1);
            border-top-color: #667eea;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* VIDEO MODAL */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        
        .modal.active { display: flex; }
        
        .modal-content {
            position: relative;
            margin: auto;
            width: 90%;
            max-width: 1200px;
            max-height: 90vh;
            background: rgba(21, 21, 21, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 40px;
            overflow-y: auto;
        }
        
        .modal-close {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 30px;
            color: white;
            cursor: pointer;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            transition: all 0.3s;
        }
        
        .modal-close:hover {
            background: #dc3545;
            transform: rotate(90deg);
        }
        
        .modal-title {
            font-size: 2em;
            margin-bottom: 30px;
            color: white;
        }
        
        .video-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .video-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
        }
        
        .video-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 32px 0 rgba(99, 102, 241, 0.3);
        }
        
        .video-player {
            width: 100%;
            height: 180px;
            background: #000;
        }
        
        .video-info { padding: 15px; }
        
        .video-title {
            font-weight: 600;
            margin-bottom: 10px;
            color: #fff;
            font-size: 0.95em;
        }
        
        .video-meta {
            color: rgba(255, 255, 255, 0.5);
            font-size: 0.85em;
            margin-bottom: 12px;
        }
        
        .video-actions { display: flex; gap: 8px; }
        
        /* ANIMATIONS */
        @keyframes cardAppear {
            0% { opacity: 0; transform: scale(0.8); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes slideInRight {
            0% { transform: translateX(100%); }
            100% { transform: translateX(0); }
        }
        
        @keyframes highlight {
            0%, 100% { background-color: transparent; }
            50% { background-color: rgba(102, 126, 234, 0.2); }
        }
        
        .stat-changed {
            animation: highlight 1s ease;
        }
        
        .value-up {
            color: #38ef7d !important;
            animation: pulse 0.5s ease;
        }
        
        .value-down {
            color: #eb3349 !important;
            animation: pulse 0.5s ease;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🎥 Stream Monitor Pro</h1>
            <p>Gerçek zamanlı yayın takibi ve kayıt yönetimi</p>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-streamers">0</div>
                <div class="stat-label">Toplam Yayıncı</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="online-streamers">0</div>
                <div class="stat-label">Online Yayıncı</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="active-recordings">0</div>
                <div class="stat-label">Aktif Kayıt</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-recordings">0</div>
                <div class="stat-label">Toplam Kayıt</div>
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="section">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('dashboard')">Dashboard</button>
                <button class="tab" onclick="switchTab('recordings')">Kayıtlar</button>
            </div>
            
            <!-- Dashboard Tab -->
            <div id="dashboard-tab" class="tab-content active">
                <h2 class="section-title">Yayıncı Yönetimi</h2>
                
                <!-- Search Bar -->
                <div class="search-container">
                    <span class="search-icon">🔍</span>
                    <input 
                        type="search" 
                        id="search-input" 
                        class="search-input" 
                        placeholder="Yayıncı ara... (Ctrl+K)"
                        oninput="filterStreamers()"
                    >
                </div>
                
                <!-- Quick Actions -->
                <div class="quick-actions">
                    <button class="quick-action-btn" onclick="startAllStreamers()">
                        🔄 Tümünü Başlat
                    </button>
                    <button class="quick-action-btn" onclick="stopAllStreamers()">
                        ⏸️ Tümünü Durdur
                    </button>
                    <button class="quick-action-btn" onclick="exportData()">
                        📊 Export JSON
                    </button>
                    <button class="quick-action-btn" onclick="refreshAll()">
                        ♻️ Yenile
                    </button>
                </div>
                
                <div class="add-streamer-form">
                    <input 
                        type="text" 
                        id="streamer-username" 
                        class="form-input" 
                        placeholder="Kullanıcı adı girin (örn: username)"
                    >
                    <button class="btn btn-success" onclick="addStreamer()">
                        ➕ Yayıncı Ekle
                    </button>
                </div>
                
                <!-- View Toggle -->
                <div class="view-controls">
                    <button class="view-btn active" onclick="toggleView('grid')" id="grid-btn">
                        ⊞ Kart
                    </button>
                    <button class="view-btn" onclick="toggleView('list')" id="list-btn">
                        ☰ Liste
                    </button>
                </div>
                
                <div id="streamers-list" class="streamer-grid">
                    <!-- Streamers will be loaded here -->
                </div>
            </div>
            
            <!-- Recordings Tab -->
            <div id="recordings-tab" class="tab-content">
                <h2 class="section-title">Kaydedilen Videolar</h2>
                
                <div id="videos-list" class="video-grid">
                    <!-- Videos will be loaded here -->
                </div>
            </div>
        </div>
    </div>
    
    <!-- Video Modal -->
    <div class="modal" id="video-modal">
        <div class="modal-content">
            <div class="modal-close" onclick="closeVideoModal()">×</div>
            <h2 class="modal-title" id="modal-title">Videolar</h2>
            <div class="video-grid" id="modal-videos"></div>
        </div>
    </div>
    
    <!-- Toast Notifications -->
    <div class="toast-container" id="toast-container"></div>
    
    <!-- Network Status -->
    <div class="network-status online" id="network-status">
        <span class="status-dot"></span>
        <span id="network-text">Canlı</span>
    </div>
    
    <!-- Keyboard Shortcuts Hint -->
    <div class="keyboard-hint">
        <kbd>Ctrl+K</kbd> Ara
        <kbd>Ctrl+N</kbd> Ekle
        <kbd>?</kbd> Yardım
    </div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loading-overlay">
        <div class="loading-spinner"></div>
    </div>
    
    <script>
        // View mode state
        let currentView = 'grid';
        
        // Cache previous data for comparison
        let previousStats = {
            total_streamers: 0,
            online_streamers: 0,
            active_recordings: 0,
            total_files: 0
        };
        
        let previousStreamers = {};
        let allStreamers = [];
        
        // Auto refresh every 10 seconds
        setInterval(loadDashboard, 10000);
        
        // Initial load
        loadDashboard();
        loadRecordings();
        
        // ========================================
        // TOAST NOTIFICATION SYSTEM
        // ========================================
        function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            const icons = {
                success: '✅',
                error: '❌',
                info: 'ℹ️'
            };
            
            toast.innerHTML = `
                <span class="toast-icon">${icons[type] || icons.info}</span>
                <span>${message}</span>
                <span class="toast-close" onclick="this.parentElement.remove()">×</span>
            `;
            
            container.appendChild(toast);
            
            setTimeout(() => {
                toast.style.animation = 'slideInRight 0.3s ease reverse';
                setTimeout(() => toast.remove(), 300);
            }, 3000);
        }
        
        // ========================================
        // NETWORK STATUS
        // ========================================
        let lastNetworkCheck = true;
        function updateNetworkStatus(isOnline) {
            const status = document.getElementById('network-status');
            const text = document.getElementById('network-text');
            
            if (isOnline !== lastNetworkCheck) {
                status.className = isOnline ? 'network-status online' : 'network-status offline';
                text.textContent = isOnline ? 'Canlı' : 'Bağlantı Yok';
                lastNetworkCheck = isOnline;
                
                if (!isOnline) {
                    showToast('Bağlantı kesildi!', 'error');
                }
            }
        }
        
        // ========================================
        // SEARCH/FILTER STREAMERS
        // ========================================
        function filterStreamers() {
            const searchText = document.getElementById('search-input').value.toLowerCase();
            const cards = document.querySelectorAll('.profile-card');
            
            let visibleCount = 0;
            cards.forEach(card => {
                const username = card.querySelector('.card-name h3').textContent.toLowerCase();
                if (username.includes(searchText)) {
                    card.style.display = '';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });
            
            if (visibleCount === 0 && searchText) {
                showToast(`"${searchText}" için sonuç bulunamadı`, 'info');
            }
        }
        
        // ========================================
        // QUICK ACTIONS
        // ========================================
        async function startAllStreamers() {
            showToast('Tüm yayıncılar başlatılıyor...', 'info');
            
            try {
                // Her yayıncı için start isteği gönder
                for (const streamer of allStreamers) {
                    await fetch('/api/start', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({username: streamer.username, site: 'CB'})
                    });
                }
                
                showToast('Tüm yayıncılar başlatıldı! 🎉', 'success');
                loadDashboard();
            } catch (error) {
                showToast('Hata oluştu!', 'error');
            }
        }
        
        async function stopAllStreamers() {
            showToast('Tüm yayıncılar durduruluyor...', 'info');
            
            try {
                // Her yayıncı için stop isteği gönder
                for (const streamer of allStreamers) {
                    await fetch('/api/stop', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({username: streamer.username, site: 'CB'})
                    });
                }
                
                showToast('Tüm yayıncılar durduruldu!', 'success');
                loadDashboard();
            } catch (error) {
                showToast('Hata oluştu!', 'error');
            }
        }
        
        function exportData() {
            const data = {
                stats: previousStats,
                streamers: allStreamers,
                timestamp: new Date().toISOString()
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `stream-monitor-${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            
            showToast('Veri dışa aktarıldı! 📊', 'success');
        }
        
        function refreshAll() {
            document.getElementById('loading-overlay').classList.add('active');
            loadDashboard();
            loadRecordings();
            setTimeout(() => {
                document.getElementById('loading-overlay').classList.remove('active');
                showToast('Sayfa yenilendi! ♻️', 'success');
            }, 500);
        }
        
        // ========================================
        // KEYBOARD SHORTCUTS
        // ========================================
        document.addEventListener('keydown', (e) => {
            // Ctrl+K - Search
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                document.getElementById('search-input').focus();
                showToast('Arama aktif', 'info');
            }
            
            // Ctrl+N - Add new streamer
            if (e.ctrlKey && e.key === 'n') {
                e.preventDefault();
                document.getElementById('streamer-username').focus();
                showToast('Yeni yayıncı ekle', 'info');
            }
            
            // ? - Help
            if (e.key === '?' && !e.ctrlKey && !e.shiftKey) {
                showToast('📚 Klavye kısayolları: Ctrl+K (Ara), Ctrl+N (Yeni Ekle)', 'info');
            }
        });
        
        // ========================================
        // SMOOTH NUMBER ANIMATION
        // ========================================
        function animateValue(element, start, end, duration) {
            const range = end - start;
            const increment = range / (duration / 16);
            let current = start;
            
            const timer = setInterval(() => {
                current += increment;
                if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                    current = end;
                    clearInterval(timer);
                }
                element.textContent = Math.round(current);
            }, 16);
        }
        
        function updateStatValue(id, newValue) {
            const element = document.getElementById(id);
            if (!element) return;
            
            const oldValue = parseInt(element.textContent) || 0;
            
            if (oldValue !== newValue) {
                animateValue(element, oldValue, newValue, 500);
                element.classList.add('stat-changed');
                setTimeout(() => element.classList.remove('stat-changed'), 1000);
                
                if (newValue > oldValue) {
                    element.classList.add('value-up');
                    setTimeout(() => element.classList.remove('value-up'), 500);
                } else if (newValue < oldValue) {
                    element.classList.add('value-down');
                    setTimeout(() => element.classList.remove('value-down'), 500);
                }
            }
        }
        
        function updateStatBadge(id, oldVal, newVal) {
            const statCard = document.getElementById(id).closest('.stat-card');
            const existingBadge = statCard.querySelector('.stat-badge');
            
            if (existingBadge) existingBadge.remove();
            
            const diff = newVal - oldVal;
            if (diff !== 0) {
                const badge = document.createElement('div');
                badge.className = 'stat-badge';
                badge.textContent = diff > 0 ? `+${diff}` : diff;
                statCard.style.position = 'relative';
                statCard.appendChild(badge);
                
                setTimeout(() => badge.remove(), 3000);
            }
        }
        
        // ========================================
        // VIEW TOGGLE
        // ========================================
        function toggleView(view) {
            currentView = view;
            document.getElementById('grid-btn').classList.toggle('active', view === 'grid');
            document.getElementById('list-btn').classList.toggle('active', view === 'list');
            const container = document.getElementById('streamers-list');
            container.classList.toggle('list-view', view === 'list');
            loadDashboard();
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab + '-tab').classList.add('active');
            if (tab === 'recordings') loadRecordings();
        }
        
        // ========================================
        // LOAD DASHBOARD
        // ========================================
        async function loadDashboard() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                updateNetworkStatus(true);
                allStreamers = data.streamers;
                
                updateStatValue('total-streamers', data.total_streamers);
                updateStatValue('online-streamers', data.online_streamers);
                updateStatValue('active-recordings', data.active_recordings);
                updateStatValue('total-recordings', data.total_files);
                
                updateStatBadge('total-streamers', previousStats.total_streamers, data.total_streamers);
                updateStatBadge('online-streamers', previousStats.online_streamers, data.online_streamers);
                updateStatBadge('active-recordings', previousStats.active_recordings, data.active_recordings);
                
                previousStats = {
                    total_streamers: data.total_streamers,
                    online_streamers: data.online_streamers,
                    active_recordings: data.active_recordings,
                    total_files: data.total_files
                };
                
                const sortedStreamers = data.streamers.sort((a, b) => {
                    if (a.is_online && !b.is_online) return -1;
                    if (!a.is_online && b.is_online) return 1;
                    return 0;
                });
                
                updateStreamersList(sortedStreamers);
                
            } catch (error) {
                console.error('Error loading dashboard:', error);
                updateNetworkStatus(false);
            }
        }
        
        function updateStreamersList(streamers) {
            const container = document.getElementById('streamers-list');
            const listMode = currentView === 'list';
            
            if (streamers.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">🎥</div>
                        <h3>Henüz Yayıncı Yok</h3>
                        <p>Takip etmek için bir yayıncı ekleyin</p>
                    </div>
                `;
                return;
            }
            
            const currentKeys = streamers.map(s => s.username).sort().join(',');
            const previousKeys = Object.keys(previousStreamers).sort().join(',');
            
            if (currentKeys !== previousKeys) {
                container.innerHTML = buildStreamerCards(streamers, listMode);
                previousStreamers = {};
                streamers.forEach(s => previousStreamers[s.username] = s);
                return;
            }
            
            streamers.forEach(s => {
                const prev = previousStreamers[s.username];
                if (!prev || 
                    prev.is_online !== s.is_online || 
                    prev.is_recording !== s.is_recording ||
                    prev.duration !== s.duration ||
                    prev.check_count !== s.check_count) {
                    updateStreamerCard(s, listMode);
                    previousStreamers[s.username] = s;
                }
            });
        }
        
        function updateStreamerCard(s, listMode) {
            const cards = document.querySelectorAll('.profile-card');
            cards.forEach(card => {
                const username = card.querySelector('.card-name h3');
                if (username && username.textContent === s.username) {
                    const statusText = card.querySelector('.card-name .status');
                    if (statusText) {
                        const newStatus = s.is_recording ? '🔴 Kaydediliyor' : (s.is_monitoring ? '▶️ İzleniyor' : '⏸ Durduruldu');
                        if (statusText.textContent !== newStatus) {
                            statusText.textContent = newStatus;
                        }
                    }
                    
                    const statItems = card.querySelectorAll('.stat-item p');
                    if (statItems[0]) statItems[0].textContent = s.is_online ? 'ONLINE' : 'OFFLINE';
                    if (statItems[1]) statItems[1].textContent = s.duration;
                    if (statItems[2]) statItems[2].textContent = s.check_count || 0;
                    
                    if (s.is_recording) {
                        card.classList.add('recording');
                    } else {
                        card.classList.remove('recording');
                    }
                }
            });
        }
        
        function buildStreamerCards(streamers, listMode) {
            return streamers.map(s => {
                const onlineIcon = s.is_online ? '🟢' : '⚫';
                const thumbnail = s.thumbnail || '';
                const profileUrl = s.profile_url || '#';
                const logoPath = '/static/logos/chaturbate.png';
                
                if (listMode) {
                    return `
                    <div class="profile-card list-mode ${s.is_recording ? 'recording' : ''}">
                        <div class="card-top ${s.is_recording ? 'recording' : ''}">
                            <div class="avatar-holder">
                                ${thumbnail ? 
                                    `<img src="${thumbnail}" alt="${s.username}" onerror="this.style.display='none'">
                                     <div class="status-badge">${onlineIcon}</div>` 
                                    : `<span class="status-icon-center">${onlineIcon}</span>`
                                }
                            </div>
                            <div class="site-logo">
                                <img src="${logoPath}" alt="Chaturbate" onerror="this.style.display='none'">
                            </div>
                        </div>
                        <div class="card-content">
                            <div class="card-name">
                                <h3 onclick="window.open('${profileUrl}', '_blank')">${s.username}</h3>
                                <p class="status">${s.is_recording ? '🔴 Kaydediliyor' : (s.is_monitoring ? '▶️ İzleniyor' : '⏸ Durduruldu')}</p>
                            </div>
                            <div class="card-stats">
                                <div class="stat-item">
                                    <h6>Durum</h6>
                                    <p>${s.is_online ? 'ONLINE' : 'OFFLINE'}</p>
                                </div>
                                <div class="stat-item">
                                    <h6>Süre</h6>
                                    <p>${s.duration}</p>
                                </div>
                                <div class="stat-item">
                                    <h6>Kontrol</h6>
                                    <p>${s.check_count || 0}</p>
                                </div>
                            </div>
                            <div class="card-actions">
                                ${s.is_monitoring ? 
                                    `<button class="btn btn-danger" onclick="stopStreamer('${s.username}')">⏸️</button>` :
                                    `<button class="btn btn-primary" onclick="startStreamer('${s.username}')">▶️</button>`
                                }
                                <button class="btn btn-videos" onclick="showVideos('${s.username}')">📹</button>
                                <button class="btn btn-danger" onclick="removeStreamer('${s.username}')">🗑️</button>
                            </div>
                        </div>
                    </div>
                `} else {
                    return `
                    <div class="profile-card ${s.is_recording ? 'recording' : ''}">
                        <div class="card-top ${s.is_recording ? 'recording' : ''}">
                            <div class="site-logo">
                                <img src="${logoPath}" alt="Chaturbate" onerror="this.style.display='none'">
                            </div>
                        </div>
                        <div class="avatar-holder">
                            ${thumbnail ? 
                                `<img src="${thumbnail}" alt="${s.username}" onerror="this.style.display='none'">
                                 <div class="status-badge">${onlineIcon}</div>` 
                                : `<span class="status-icon-center">${onlineIcon}</span>`
                            }
                        </div>
                        <div class="card-name">
                            <h3 onclick="window.open('${profileUrl}', '_blank')">${s.username}</h3>
                            <p class="status">${s.is_recording ? '🔴 Kaydediliyor' : (s.is_monitoring ? '▶️ İzleniyor' : '⏸ Durduruldu')}</p>
                        </div>
                        <div class="card-stats">
                            <div class="stat-item">
                                <h6>Durum</h6>
                                <p>${s.is_online ? 'ONLINE' : 'OFFLINE'}</p>
                            </div>
                            <div class="stat-item">
                                <h6>Süre</h6>
                                <p>${s.duration}</p>
                            </div>
                            <div class="stat-item">
                                <h6>Kontrol</h6>
                                <p>${s.check_count || 0}</p>
                            </div>
                        </div>
                        <div class="card-actions">
                            ${s.is_monitoring ? 
                                `<button class="btn btn-danger" onclick="stopStreamer('${s.username}')">⏸️ Durdur</button>` :
                                `<button class="btn btn-primary" onclick="startStreamer('${s.username}')">▶️ Başlat</button>`
                            }
                            <button class="btn btn-videos" onclick="showVideos('${s.username}')">📹</button>
                            <button class="btn btn-danger" onclick="removeStreamer('${s.username}')">🗑️</button>
                        </div>
                    </div>
                `}
            }).join('');
        }
        
        // ========================================
        // RECORDINGS
        // ========================================
        async function loadRecordings() {
            try {
                const response = await fetch('/api/recordings');
                const data = await response.json();
                
                const container = document.getElementById('videos-list');
                
                if (data.recordings.length === 0) {
                    container.innerHTML = '<p style="text-align: center; color: rgba(255,255,255,0.5); padding: 40px;">Henüz kayıt yok</p>';
                    return;
                }
                
                container.innerHTML = data.recordings.map(r => `
                    <div class="video-card">
                        <video class="video-player" controls>
                            <source src="/api/video/${encodeURIComponent(r.path)}" type="video/mp4">
                        </video>
                        <div class="video-info">
                            <div class="video-title">📹 ${r.username}</div>
                            <div class="video-meta">
                                📅 ${r.date}<br>
                                💾 ${r.size}
                            </div>
                            <div class="video-actions">
                                <button class="btn btn-primary" onclick="downloadVideo('${r.path}')">
                                    ⬇️ İndir
                                </button>
                                <button class="btn btn-danger" onclick="deleteVideo('${r.path}')">
                                    🗑️ Sil
                                </button>
                            </div>
                        </div>
                    </div>
                `).join('');
                
            } catch (error) {
                console.error('Error loading recordings:', error);
            }
        }
        
        async function showVideos(username) {
            const modal = document.getElementById('video-modal');
            const title = document.getElementById('modal-title');
            const grid = document.getElementById('modal-videos');
            
            title.textContent = '📹 ' + username + ' - Kayıtlar';
            
            try {
                const response = await fetch('/api/recordings');
                const data = await response.json();
                
                const userVideos = data.recordings.filter(r => r.username === username);
                
                if (userVideos.length === 0) {
                    grid.innerHTML = '<p style="text-align: center; color: rgba(255,255,255,0.5); padding: 40px;">Henüz kayıt yok</p>';
                } else {
                    grid.innerHTML = userVideos.map(r => `
                        <div class="video-card">
                            <video class="video-player" controls preload="metadata">
                                <source src="/api/video/${encodeURIComponent(r.path)}" type="video/mp4">
                            </video>
                            <div class="video-info">
                                <div class="video-title">📹 ${r.filename}</div>
                                <div class="video-meta">📅 ${r.date}<br>💾 ${r.size}</div>
                                <div class="video-actions">
                                    <button class="btn btn-primary" onclick="downloadVideo('${r.path}')">⬇️</button>
                                    <button class="btn btn-danger" onclick="deleteVideo('${r.path}')">🗑️</button>
                                </div>
                            </div>
                        </div>
                    `).join('');
                }
                
                modal.classList.add('active');
            } catch (error) {
                console.error(error);
            }
        }
        
        function closeVideoModal() {
            document.getElementById('video-modal').classList.remove('active');
        }
        
        // ========================================
        // STREAMER ACTIONS
        // ========================================
        async function addStreamer() {
            const username = document.getElementById('streamer-username').value.trim();
            if (!username) {
                showToast('Lütfen kullanıcı adı girin', 'error');
                return;
            }
            
            try {
                document.getElementById('loading-overlay').classList.add('active');
                
                const response = await fetch('/api/add', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: username, site: 'CB'})
                });
                
                const data = await response.json();
                
                document.getElementById('loading-overlay').classList.remove('active');
                
                if (data.success) {
                    showToast(`${username} eklendi ve izleme başlatıldı! 🎉`, 'success');
                    document.getElementById('streamer-username').value = '';
                    loadDashboard();
                } else {
                    showToast(data.message || 'Hata oluştu', 'error');
                }
            } catch (error) {
                document.getElementById('loading-overlay').classList.remove('active');
                showToast('Bağlantı hatası', 'error');
            }
        }
        
        async function removeStreamer(username) {
            if (!confirm(`${username} yayıncısını silmek istediğinize emin misiniz?`)) return;
            
            try {
                const response = await fetch('/api/remove', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: username, site: 'CB'})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast(`${username} silindi`, 'success');
                    loadDashboard();
                } else {
                    showToast(data.message || 'Hata oluştu', 'error');
                }
            } catch (error) {
                showToast('Bağlantı hatası', 'error');
            }
        }
        
        async function startStreamer(username) {
            try {
                const response = await fetch('/api/start', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: username, site: 'CB'})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast(`${username} izleme başlatıldı ▶️`, 'success');
                    loadDashboard();
                }
            } catch (error) {
                showToast('Bağlantı hatası', 'error');
            }
        }
        
        async function stopStreamer(username) {
            try {
                const response = await fetch('/api/stop', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({username: username, site: 'CB'})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast(`${username} izleme durduruldu ⏸️`, 'info');
                    loadDashboard();
                }
            } catch (error) {
                showToast('Bağlantı hatası', 'error');
            }
        }
        
        function downloadVideo(path) {
            window.open(`/api/download/${encodeURIComponent(path)}`, '_blank');
        }
        
        async function deleteVideo(path) {
            if (!confirm('Bu videoyu silmek istediğinize emin misiniz?')) return;
            
            try {
                const response = await fetch('/api/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: path})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showToast('Video silindi', 'success');
                    loadRecordings();
                    loadDashboard();
                } else {
                    showToast(data.message || 'Hata oluştu', 'error');
                }
            } catch (error) {
                showToast('Bağlantı hatası', 'error');
            }
        }
        
        // Modal click outside to close
        document.getElementById('video-modal').addEventListener('click', function(e) {
            if (e.target === this) closeVideoModal();
        });
    </script>
</body>
</html>
'''

# ============================================================================
# API Routes (AYNI)
# ============================================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    streamers_data = []
    online_count = 0
    recording_count = 0
    
    for key, streamer in monitor.streamers.items():
        duration_str = "-"
        if streamer.is_recording and streamer.recording_start_time:
            duration = datetime.now() - streamer.recording_start_time
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            seconds = int(duration.total_seconds() % 60)
            
            if hours > 0:
                duration_str = f"{hours}s {minutes:02d}d {seconds:02d}sn"
            else:
                duration_str = f"{minutes:02d}d {seconds:02d}sn"
        
        if streamer.is_online:
            online_count += 1
        if streamer.is_recording:
            recording_count += 1
        
        snapshot_path = os.path.join('static', 'users', f'{streamer.username}.jpg')
        if os.path.exists(snapshot_path):
            thumbnail_url = f'/static/users/{streamer.username}.jpg'
        else:
            thumbnail_url = streamer.site.get_thumbnail_url(streamer.username)
        
        profile_url = streamer.site.get_profile_url(streamer.username)
        
        streamers_data.append({
            'username': streamer.username,
            'site': streamer.site.abbreviation,
            'is_online': streamer.is_online,
            'is_recording': streamer.is_recording,
            'is_monitoring': streamer.is_monitoring,
            'duration': duration_str,
            'check_count': streamer.check_count,
            'thumbnail': thumbnail_url,
            'profile_url': profile_url
        })
    
    total_files = 0
    rec_dir = app.config['RECORDINGS_DIR']
    if os.path.exists(rec_dir):
        for root, dirs, files in os.walk(rec_dir):
            total_files += len([f for f in files if f.endswith('.mp4')])
    
    return jsonify({
        'total_streamers': len(monitor.streamers),
        'online_streamers': online_count,
        'active_recordings': recording_count,
        'total_files': total_files,
        'streamers': streamers_data
    })

@app.route('/api/recordings')
def api_recordings():
    recordings = []
    rec_dir = app.config['RECORDINGS_DIR']
    
    if os.path.exists(rec_dir):
        for root, dirs, files in os.walk(rec_dir):
            for filename in files:
                if filename.endswith('.mp4'):
                    full_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(full_path, rec_dir)
                    
                    # CRITICAL: Convert Windows backslash to forward slash for URLs
                    rel_path = rel_path.replace('\\', '/')
                    
                    # CRITICAL: Parse filename correctly (username may contain underscores)
                    # Format: {site}_{username}_{date}_{time}.mp4
                    # Example: CB_lili_and_niki_20251017_180452.mp4
                    parts = filename.replace('.mp4', '').split('_')
                    
                    if len(parts) >= 4:
                        site = parts[0]
                        date_part = parts[-2]
                        time_part = parts[-1]
                        # Username is everything between site and date
                        username = '_'.join(parts[1:-2])
                    else:
                        username = parts[1] if len(parts) > 1 else 'unknown'
                        date_part = parts[2] if len(parts) > 2 else ''
                        time_part = parts[3] if len(parts) > 3 else ''
                    
                    try:
                        date_str = f"{date_part} {time_part}"
                        date_obj = datetime.strptime(date_str, "%Y%m%d %H%M%S")
                        date_formatted = date_obj.strftime("%d.%m.%Y %H:%M")
                    except:
                        date_formatted = "Bilinmiyor"
                    
                    size_bytes = os.path.getsize(full_path)
                    size_mb = size_bytes / (1024 * 1024)
                    size_str = f"{size_mb:.2f} MB"
                    
                    recordings.append({
                        'path': rel_path,
                        'filename': filename,
                        'username': username,
                        'date': date_formatted,
                        'size': size_str,
                        'size_bytes': size_bytes
                    })
        
        recordings.sort(key=lambda x: x['size_bytes'], reverse=True)
    
    return jsonify({
        'recordings': recordings,
        'total': len(recordings)
    })

@app.route('/api/add', methods=['POST'])
def api_add():
    data = request.json
    username = data.get('username')
    site = data.get('site', 'CB')
    
    if not username:
        return jsonify({'success': False, 'message': 'Kullanıcı adı gerekli'})
    
    if monitor.add_streamer(username, site):
        config.add_streamer(username, site)
        monitor.start_monitoring(username, site)
        return jsonify({'success': True, 'message': 'Yayıncı eklendi'})
    else:
        return jsonify({'success': False, 'message': 'Yayıncı zaten listede'})

@app.route('/api/remove', methods=['POST'])
def api_remove():
    data = request.json
    username = data.get('username')
    site = data.get('site')
    
    if monitor.remove_streamer(username, site):
        config.remove_streamer(username, site)
        return jsonify({'success': True, 'message': 'Yayıncı silindi'})
    else:
        return jsonify({'success': False, 'message': 'Yayıncı bulunamadı'})

@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.json
    username = data.get('username')
    site = data.get('site')
    
    monitor.start_monitoring(username, site)
    return jsonify({'success': True, 'message': 'İzleme başlatıldı'})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    data = request.json
    username = data.get('username')
    site = data.get('site')
    
    monitor.stop_monitoring(username, site)
    return jsonify({'success': True, 'message': 'İzleme durduruldu'})

@app.route('/api/video/<path:filename>')
def api_video(filename):
    rec_dir = app.config['RECORDINGS_DIR']
    
    # Convert URL forward slashes to OS-specific path separator
    filename = filename.replace('/', os.sep)
    file_path = os.path.join(rec_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Video bulunamadı'}), 404
    
    return send_file(file_path, mimetype='video/mp4')

@app.route('/api/download/<path:filename>')
def api_download(filename):
    rec_dir = app.config['RECORDINGS_DIR']
    
    # Convert URL forward slashes to OS-specific path separator
    filename = filename.replace('/', os.sep)
    file_path = os.path.join(rec_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Video bulunamadı'}), 404
    
    return send_file(file_path, as_attachment=True, download_name=os.path.basename(filename))

@app.route('/api/delete', methods=['POST'])
def api_delete():
    data = request.json
    path = data.get('path')
    
    if not path:
        return jsonify({'success': False, 'message': 'Path gerekli'})
    
    rec_dir = app.config['RECORDINGS_DIR']
    
    # Convert URL forward slashes to OS-specific path separator
    path = path.replace('/', os.sep)
    file_path = os.path.join(rec_dir, path)
    
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Dosya bulunamadı'})
    
    try:
        os.remove(file_path)
        return jsonify({'success': True, 'message': 'Video silindi'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ============================================================================
# Main
# ============================================================================

def init_monitor():
    global monitor, config
    
    print("\n" + "="*70)
    print("STREAM MONITOR PRO - FULL FEATURED")
    print("="*70)
    
    config = Config()
    monitor = StreamMonitor(check_interval=60)
    
    loaded_count = 0
    for s in config.get_streamers():
        if monitor.add_streamer(s['username'], s['site']):
            loaded_count += 1
    
    print(f"\n✓ {loaded_count} yayıncı yüklendi")
    
    if loaded_count > 0:
        print("\n" + "="*70)
        print("OTOMATIK İZLEME BAŞLATILIYOR...")
        print("="*70)
        
        started_count = monitor.start_all()
        print(f"\n✓ {started_count} yayıncı için izleme aktif!")
    
    print("\n" + "="*70)
    print("WEB ARAYÜZÜ HAZIR!")
    print("="*70)
    print("\n🌐 Tarayıcınızda açın: http://localhost:5000")
    print("\n✨ Yeni Özellikler:")
    print("   • 🍞 Toast Notifications")
    print("   • 🔍 Search Bar (Ctrl+K)")
    print("   • ⚡ Quick Actions")
    print("   • 📡 Network Status")
    print("   • ⌨️ Keyboard Shortcuts")
    print("   • 📊 Export Data")
    print("   • 🔔 Stat Badges")
    print("   • ⏳ Loading Overlay")
    print("   • 📭 Empty State")
    print("\n⌨️  Klavye Kısayolları:")
    print("   Ctrl+K → Arama")
    print("   Ctrl+N → Yeni Yayıncı")
    print("   ?      → Yardım")
    print("\nKapatmak için: Ctrl+C")
    print("="*70 + "\n")

def run_server(host='0.0.0.0', port=5000, debug=False):
    init_monitor()
    app.run(host=host, port=port, debug=debug, use_reloader=False)

if __name__ == '__main__':
    try:
        run_server(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\nKapatılıyor...")
        if monitor:
            monitor.shutdown()
        print("Güle güle!")