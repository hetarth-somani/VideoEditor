"""
YouTube Metadata Analysis System
Complete implementation for video editing suitability analysis
"""

import os
import requests
import math
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from collections import Counter

class YouTubeVideoAnalyzer:
    """
    Analyzes YouTube videos using metadata from YouTube Data API
    to determine suitability for video editing purposes.
    """
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        
        # Configure retry strategy for API calls
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        
        # Scoring weights for different factors
        self.weights = {
            'keyword_match': 0.25,
            'duration_score': 0.20,
            'license_score': 0.15,
            'freshness_score': 0.15,
            'engagement_score': 0.10,
            'quality_indicators': 0.10,
            'tag_relevance': 0.05
        }
        
        # Creative Commons license indicators
        self.cc_licenses = [
            'creativeCommons',
            'creative commons',
            'cc by',
            'cc0',
            'public domain',
            'royalty free',
            'copyright free'
        ]
        
        # Quality indicators in titles/descriptions
        self.quality_keywords = [
            '4k', 'hd', 'high quality', 'professional', 'cinematic',
            'stock footage', 'b-roll', 'background', 'overlay',
            'transition', 'effect', 'template', 'royalty-free'
        ]
        
        # Negative indicators (lower quality/unsuitable)
        self.negative_keywords = [
            'reaction', 'review', 'commentary', 'podcast', 'interview',
            'live stream', 'gameplay', 'tutorial', 'vlog', 'unboxing'
        ]
    
    def analyze_videos(self, search_query, max_results=50, filters=None):
        """Main method to search and analyze YouTube videos"""
        try:
            # Get video metadata from YouTube API
            videos = self._search_videos(search_query, max_results)
            
            if not videos:
                return []
            
            # Get detailed video information
            video_ids = [video['id']['videoId'] for video in videos]
            detailed_videos = self._get_video_details(video_ids)
            
            # Analyze and score each video
            analyzed_videos = []
            for video in detailed_videos:
                score_data = self._analyze_video(video, search_query, filters)
                if score_data['total_score'] > 0.3:  # Minimum threshold
                    analyzed_videos.append(score_data)
            
            # Sort by confidence score
            analyzed_videos.sort(key=lambda x: x['total_score'], reverse=True)
            
            return analyzed_videos
            
        except Exception as e:
            print(f"Error in video analysis: {str(e)}")
            return []
    
    def _search_videos(self, query, max_results):
        """Search for videos using YouTube Data API"""
        url = 'https://www.googleapis.com/youtube/v3/search'
        params = {
            'part': 'snippet',
            'q': query,
            'maxResults': min(max_results, 50),  # API limit
            'type': 'video',
            'videoEmbeddable': 'true',
            'videoSyndicated': 'true',
            'order': 'relevance',
            'key': self.api_key
        }
        
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            print(f"Search API error: {response.status_code}")
            return []
    
    def _get_video_details(self, video_ids):
        """Get detailed video information including duration, license, stats"""
        if not video_ids:
            return []
            
        url = 'https://www.googleapis.com/youtube/v3/videos'
        params = {
            'part': 'snippet,contentDetails,statistics,status',
            'id': ','.join(video_ids),
            'key': self.api_key
        }
        
        response = self.session.get(url, params=params)
        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            print(f"Details API error: {response.status_code}")
            return []
    
    def _analyze_video(self, video, search_query, filters=None):
        """Analyze a single video and calculate confidence score"""
        snippet = video.get('snippet', {})
        content_details = video.get('contentDetails', {})
        statistics = video.get('statistics', {})
        status = video.get('status', {})
        
        # Extract metadata
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        tags = snippet.get('tags', [])
        duration = content_details.get('duration', 'PT0S')
        license_type = status.get('license', 'youtube')
        upload_date = snippet.get('publishedAt', '')
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        
        # Calculate individual scores
        scores = {
            'keyword_match': self._calculate_keyword_score(title, description, search_query),
            'duration_score': self._calculate_duration_score(duration, filters),
            'license_score': self._calculate_license_score(license_type, title, description),
            'freshness_score': self._calculate_freshness_score(upload_date),
            'engagement_score': self._calculate_engagement_score(view_count, like_count),
            'quality_indicators': self._calculate_quality_score(title, description),
            'tag_relevance': self._calculate_tag_score(tags, search_query)
        }
        
        # Calculate weighted total score
        total_score = sum(scores[key] * self.weights[key] for key in scores)
        
        # Parse duration to seconds for display
        duration_seconds = self._parse_duration(duration)
        
        return {
            'video_id': video['id'],
            'title': snippet.get('title', ''),
            'description': snippet.get('description', '')[:300] + '...' if len(snippet.get('description', '')) > 300 else snippet.get('description', ''),
            'thumbnail': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
            'channel': snippet.get('channelTitle', ''),
            'duration': duration_seconds,
            'duration_formatted': self._format_duration(duration_seconds),
            'upload_date': upload_date,
            'view_count': view_count,
            'like_count': like_count,
            'license_type': license_type,
            'watch_url': f'https://www.youtube.com/watch?v={video["id"]}',
            'embed_url': f'https://www.youtube.com/embed/{video["id"]}',
            'total_score': round(total_score, 3),
            'score_breakdown': {k: round(v, 3) for k, v in scores.items()},
            'suitability_reason': self._generate_suitability_reason(scores, total_score)
        }
    
    def _calculate_keyword_score(self, title, description, search_query):
        """Calculate relevance based on keyword matching"""
        query_words = search_query.lower().split()
        text = f"{title} {description}"
        
        # Exact phrase match (highest score)
        if search_query.lower() in text:
            return 1.0
        
        # Individual word matches
        matches = sum(1 for word in query_words if word in text)
        word_score = matches / len(query_words) if query_words else 0
        
        # Negative keywords penalty
        negative_penalty = sum(0.1 for neg in self.negative_keywords if neg in text)
        
        return max(0, word_score - negative_penalty)
    
    def _calculate_duration_score(self, duration, filters):
        """Score based on video duration suitability for editing"""
        seconds = self._parse_duration(duration)
        
        # Apply user filters if provided
        if filters and 'min_duration' in filters:
            if seconds < filters['min_duration']:
                return 0
        if filters and 'max_duration' in filters:
            if seconds > filters['max_duration']:
                return 0
        
        # Optimal duration ranges for editing
        if 10 <= seconds <= 300:  # 10 seconds to 5 minutes - excellent
            return 1.0
        elif 5 <= seconds <= 600:  # 5 seconds to 10 minutes - good
            return 0.8
        elif 1 <= seconds <= 1800:  # 1 second to 30 minutes - acceptable
            return 0.6
        else:
            return 0.2  # Too short or too long
    
    def _calculate_license_score(self, license_type, title, description):
        """Score based on license type and Creative Commons indicators"""
        score = 0
        
        # Official Creative Commons license
        if license_type == 'creativeCommons':
            score = 1.0
        
        # Check for CC indicators in title/description
        text = f"{title} {description}"
        cc_mentions = sum(1 for cc in self.cc_licenses if cc in text)
        if cc_mentions > 0:
            score = max(score, 0.8)
        
        # Standard YouTube license gets lower score
        if license_type == 'youtube' and score == 0:
            score = 0.3
        
        return score
    
    def _calculate_freshness_score(self, upload_date):
        """Score based on how recent the video is"""
        try:
            upload_dt = datetime.strptime(upload_date, '%Y-%m-%dT%H:%M:%SZ')
            days_old = (datetime.now() - upload_dt).days
            
            if days_old <= 30:  # Very fresh
                return 1.0
            elif days_old <= 90:  # Recent
                return 0.8
            elif days_old <= 365:  # Within a year
                return 0.6
            elif days_old <= 1095:  # Within 3 years
                return 0.4
            else:  # Older content
                return 0.2
        except:
            return 0.5  # Default if date parsing fails
    
    def _calculate_engagement_score(self, view_count, like_count):
        """Score based on engagement metrics"""
        if view_count == 0:
            return 0
        
        # Like ratio (likes per 1000 views)
        like_ratio = (like_count / view_count) * 1000 if view_count > 0 else 0
        
        # View count score (logarithmic scale)
        view_score = min(1.0, math.log10(max(1, view_count)) / 7)  # 10M views = 1.0
        
        # Combine metrics
        return (like_ratio * 0.3 + view_score * 0.7)
    
    def _calculate_quality_score(self, title, description):
        """Score based on quality indicators in metadata"""
        text = f"{title} {description}"
        
        # Positive quality indicators
        quality_score = sum(0.2 for keyword in self.quality_keywords if keyword in text)
        
        # Negative indicators
        negative_score = sum(0.15 for keyword in self.negative_keywords if keyword in text)
        
        return max(0, min(1.0, quality_score - negative_score))
    
    def _calculate_tag_score(self, tags, search_query):
        """Score based on tag relevance"""
        if not tags:
            return 0
        
        query_words = set(search_query.lower().split())
        tag_words = set(' '.join(tags).lower().split())
        
        # Calculate intersection
        intersection = query_words.intersection(tag_words)
        if not query_words:
            return 0
        
        return len(intersection) / len(query_words)
    
    def _parse_duration(self, duration):
        """Parse ISO 8601 duration to seconds"""
        try:
            # Remove PT prefix
            duration = duration.replace('PT', '')
            
            seconds = 0
            # Parse hours
            if 'H' in duration:
                hours, duration = duration.split('H')
                seconds += int(hours) * 3600
            
            # Parse minutes
            if 'M' in duration:
                minutes, duration = duration.split('M')
                seconds += int(minutes) * 60
            
            # Parse seconds
            if 'S' in duration:
                secs = duration.replace('S', '')
                seconds += int(float(secs))
            
            return seconds
        except:
            return 0
    
    def _format_duration(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _generate_suitability_reason(self, scores, total_score):
        """Generate human-readable reason for suitability score"""
        reasons = []
        
        if scores['license_score'] > 0.7:
            reasons.append("Creative Commons or royalty-free license")
        if scores['keyword_match'] > 0.8:
            reasons.append("High keyword relevance")
        if scores['duration_score'] > 0.8:
            reasons.append("Optimal duration for editing")
        if scores['quality_indicators'] > 0.6:
            reasons.append("Quality content indicators")
        if scores['engagement_score'] > 0.6:
            reasons.append("Good engagement metrics")
        if scores['freshness_score'] > 0.7:
            reasons.append("Recent upload")
        
        if not reasons:
            if total_score > 0.6:
                reasons.append("Good overall match")
            elif total_score > 0.4:
                reasons.append("Moderate match")
            else:
                reasons.append("Basic match")
        
        return "; ".join(reasons)

# Test the implementation
if __name__ == "__main__":
    print("✅ YouTube Metadata Analysis System - Clean Implementation Ready!")