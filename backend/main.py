import sys
import os

# Point to the actual backend code
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "网站制作", "backend"))

from app.main import app
