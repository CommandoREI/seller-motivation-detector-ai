"""
Usage Tracking System for Seller Motivation Detector AI
Tracks audio transcription minutes and analysis counts per user per month
"""

import json
import os
from datetime import datetime
from typing import Dict, Tuple

class UsageTracker:
    def __init__(self, data_file='usage_data.json'):
        """Initialize usage tracker with persistent storage"""
        self.data_file = data_file
        self.monthly_audio_limit = 500  # minutes per user per month
        self.monthly_analysis_limit = 200  # analyses per user per month
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load usage data from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_data(self):
        """Save usage data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _get_current_month(self) -> str:
        """Get current month key (YYYY-MM format)"""
        return datetime.now().strftime('%Y-%m')
    
    def _get_user_data(self, user_id: str) -> Dict:
        """Get or create user data structure"""
        if user_id not in self.data:
            self.data[user_id] = {}
        
        current_month = self._get_current_month()
        if current_month not in self.data[user_id]:
            self.data[user_id][current_month] = {
                'audio_minutes': 0.0,
                'analysis_count': 0,
                'last_updated': datetime.now().isoformat()
            }
        
        return self.data[user_id][current_month]
    
    def check_audio_limit(self, user_id: str, duration_minutes: float) -> Tuple[bool, float]:
        """
        Check if user can transcribe audio of given duration
        Returns: (can_proceed, remaining_minutes)
        """
        user_data = self._get_user_data(user_id)
        used_minutes = user_data['audio_minutes']
        remaining = self.monthly_audio_limit - used_minutes
        
        can_proceed = (used_minutes + duration_minutes) <= self.monthly_audio_limit
        return can_proceed, remaining
    
    def check_analysis_limit(self, user_id: str) -> Tuple[bool, int]:
        """
        Check if user can perform another analysis
        Returns: (can_proceed, remaining_analyses)
        """
        user_data = self._get_user_data(user_id)
        used_count = user_data['analysis_count']
        remaining = self.monthly_analysis_limit - used_count
        
        can_proceed = used_count < self.monthly_analysis_limit
        return can_proceed, remaining
    
    def record_audio_usage(self, user_id: str, duration_minutes: float):
        """Record audio transcription usage"""
        user_data = self._get_user_data(user_id)
        user_data['audio_minutes'] += duration_minutes
        user_data['last_updated'] = datetime.now().isoformat()
        self._save_data()
    
    def record_analysis_usage(self, user_id: str):
        """Record analysis usage"""
        user_data = self._get_user_data(user_id)
        user_data['analysis_count'] += 1
        user_data['last_updated'] = datetime.now().isoformat()
        self._save_data()
    
    def get_usage_stats(self, user_id: str) -> Dict:
        """Get current usage statistics for user"""
        user_data = self._get_user_data(user_id)
        
        return {
            'audio_minutes_used': user_data['audio_minutes'],
            'audio_minutes_remaining': self.monthly_audio_limit - user_data['audio_minutes'],
            'audio_minutes_limit': self.monthly_audio_limit,
            'analyses_used': user_data['analysis_count'],
            'analyses_remaining': self.monthly_analysis_limit - user_data['analysis_count'],
            'analyses_limit': self.monthly_analysis_limit,
            'current_month': self._get_current_month(),
            'last_updated': user_data.get('last_updated', 'Never')
        }
    
    def get_all_usage(self) -> Dict:
        """Get usage statistics for all users (admin view)"""
        current_month = self._get_current_month()
        all_stats = {}
        
        for user_id, user_data in self.data.items():
            if current_month in user_data:
                all_stats[user_id] = {
                    'audio_minutes': user_data[current_month]['audio_minutes'],
                    'analysis_count': user_data[current_month]['analysis_count'],
                    'last_updated': user_data[current_month].get('last_updated', 'Unknown')
                }
        
        return all_stats
