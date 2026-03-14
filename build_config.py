"""
Shared configuration: paths, author info, and social link definitions.
"""

from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_PATH = BASE_DIR / "template.html"
OUTPUT_PATH = BASE_DIR / "index.html"
RESUME_TEMPLATE_PATH = BASE_DIR / "resume_template.tex"
RESUME_OUTPUT_PATH = BASE_DIR / "resume.pdf"

# Author identity (used for highlighting in publications)
AUTHOR_NAME = "Dogan, A. H."
AUTHOR_NAME_ALT = "Doğan, A. H."
AUTHOR_DISPLAY_NAME = "Adnan Harun Dogan"

# Social platform URL templates — {id} is replaced with the user's ID
URL_TEMPLATES = {
    "email": "mailto:{id}",
    "github": "https://github.com/{id}",
    "linkedin": "https://linkedin.com/in/{id}",
    "google_scholar": "https://scholar.google.com/citations?user={id}",
    "twitter": "https://twitter.com/{id}",
    "orcid": "https://orcid.org/{id}",
    "acm": "https://dl.acm.org/profile/{id}",
    "ieee": "https://ieeexplore.ieee.org/author/{id}",
    "dblp": "https://dblp.org/pid/{id}",
    "semantic_scholar": "https://www.semanticscholar.org/author/{id}",
}

# Human-readable names for each platform
LINK_NAMES = {
    "email": "Email",
    "github": "GitHub",
    "linkedin": "LinkedIn",
    "google_scholar": "Google Scholar",
    "twitter": "Twitter",
    "orcid": "ORCID",
    "acm": "ACM DL",
    "ieee": "IEEE Xplore",
    "dblp": "DBLP",
    "semantic_scholar": "Semantic Scholar",
}

# Font Awesome / Academicons CSS classes for each platform
LINK_ICONS = {
    "email": "fas fa-envelope",
    "github": "fab fa-github",
    "linkedin": "fab fa-linkedin",
    "google_scholar": "ai ai-google-scholar",
    "twitter": "fab fa-twitter",
    "orcid": "ai ai-orcid",
    "acm": "ai ai-acm",
    "ieee": "ai ai-ieee",
    "dblp": "ai ai-dblp",
    "semantic_scholar": "ai ai-semantic-scholar",
}

# Sidebar link grouping
PRIMARY_LINKS = ["github", "linkedin", "google_scholar"]
SECONDARY_CATEGORIES = {
    "Academic Profiles": ["acm", "ieee", "dblp", "semantic_scholar", "orcid"],
    "Social": ["twitter", "email"],
}
