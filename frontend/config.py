"""
Shared configuration for the APIC frontend.
"""

import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
