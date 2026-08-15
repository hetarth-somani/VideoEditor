# Clean YouTube Analyzer Implementation

# Initialize YouTube analyzer
youtube_analyzer = None
if os.getenv('YOUTUBE_API_KEY'):
    youtube_analyzer = YouTubeVideoAnalyzer(os.getenv('YOUTUBE_API_KEY'))

# API configurations
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

# Define ImageMagick path for Windows
IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"