class ScraperException(Exception):
    """Base Web Scraping Exception"""

class RateLimitException(ScraperException):
    """Too many requests"""