# Adnan Harun Dogan - Personal Website

A clean, simple single-page personal website for GitHub Pages with data-driven content using YAML files.

## Features

- **Data-Driven**: All content stored in easy-to-edit YAML files
- **Smart Link Generation**: Just provide IDs (e.g., GitHub username) instead of full URLs
- **Auto-fetch Publications**: Fetch from Google Scholar automatically using the scholarly library
- **Bio Section**: Short bio with profile image and social links
- **Resume**: Web-based resume with education and experience
- **News**: Latest updates and announcements
- **Timeline**: Dual timeline showing internships/education on one side and papers/projects on the other
- **Responsive Design**: Works beautifully on desktop and mobile

## Quick Start

### 1. Add Your Profile Picture
Place your profile image as `profile.jpeg` (or `profile.jpg`) in the root directory (200x200px recommended, square aspect ratio)

### 2. Update YAML Data Files

All content is stored in the `data/` directory. Edit these files:

Dates use ISO format with partial precision: `YYYY`, `YYYY-MM`, or
`YYYY-MM-DD` (plus the literal `Present`). They render human-readable at build
time, e.g. `2025-03` shows as "March 2025". The examples below use generic
placeholders.

#### `data/bio.yaml` - identity, bio text, social links
```yaml
name: "Jane Doe"
title: "PhD Student"
affiliation: "Example University"
profile_image: "assets/img/profile-sm.jpeg"
site_url: "https://janedoe.github.io"
short_bio: "One or two sentences for the sidebar."
bio: |
  Full bio (HTML allowed); blank lines separate paragraphs.
social:              # give IDs/usernames only - full URLs are generated
  email: "jane@example.com"
  github: "janedoe"
  linkedin: "jane-doe"
  google_scholar: "XXXXXXXX"
  orcid: "0000-0000-0000-0000"
custom_links:        # extra sidebar links
  - name: "Resume"
    url: "resume.pdf"
```
Supported social platforms: `email`, `github`, `linkedin`, `google_scholar`,
`acm`, `ieee`, `dblp`, `semantic_scholar`, `twitter`, `orcid`.

#### `data/education.yaml` - degrees
```yaml
education:
  - degree: "PhD in Computer Science"
    institution: "Example University"
    location: "City, Country"
    start_date: "2023"
    end_date: "Present"
    logo: "assets/img/logos/example.png"   # optional
    timelined: true                        # also show on the Timeline page
```

#### `data/experience.yaml` - work / internships
```yaml
experience:
  - position: "Research Intern"
    company: "Example Lab"
    location: "City, Country"
    start_date: "2024-06"
    end_date: "2024-09"
    advisor: "Prof. A. Adviser"        # optional
    commitment: "Full-time, 3 months"  # optional
    logo: "assets/img/logos/example.png"
    timelined: true
    bullets:
      - "What you did, one line each."
```

#### `data/research.yaml` and `data/teaching.yaml`
Same shape as `experience.yaml` (`position`, `company`, dates, `bullets`,
`logo`, `timelined`): `research` holds research positions, `teaching` holds
TA/teaching entries.

#### `data/extracurricular.yaml` - honors and skills
```yaml
honors:
  - title: "Best Paper Award"
    organization: "Some Conference"
    date: "2024"
    logo: "assets/img/logos/example.png"   # optional
skills:
  - "Python"
  - "PyTorch"
```

#### `data/publications.yaml` - papers
```yaml
papers:
  - title: "A Paper Title"
    authors: "Doe, J., Coauthor, A."
    venue: "Conference on Examples"
    venue_short: "CoE 2025"               # colored tag
    venue_link: "https://example.org"     # optional, makes the tag clickable
    date: "2025"
    image: "assets/img/publications/paper.png"  # thumbnail (selected works)
    selected: true   # show on the About page with image
    resume: true     # list on the CV page
    timelined: true  # show on the Timeline page
    abstract: |      # optional; rendered on the paper's project page
      ## Problem
      Markdown with '## ' sections, '|' tables, and MathJax math such as
      \(a^2 + b^2 = c^2\) inline or \[ E = mc^2 \] as a display equation.
    links:
      - name: "Paper"
        url: "https://arxiv.org/abs/0000.00000"
      - name: "GitHub"
        url: "https://github.com/user/repo"
```

#### `data/news.yaml` - news feed
```yaml
items:
  - date: "2025-03"
    content: "Something happened."
    tags: ["publication"]   # publication | degree | internship | award
    link: "https://example.org"   # optional
```

#### `data/blogs.yaml` - blog listings + tag tree
```yaml
tag_tree:              # child tags inherit ancestors when filtering
  machine-learning:
    - reinforcement-learning
blogs:
  - title: "A Blog Post"
    date: "2025-01"
    description: "One-line summary."
    path: "blogs/my-post/index.html"
    selected: true     # feature on the About page
    tags: [reinforcement-learning]
```

#### `data/works.yaml` - open-source projects
```yaml
works:
  - title: "my-project"
    description: "One line for the card."
    url: "https://github.com/user/my-project"
    tags: ["Python", "PyTorch"]   # known tech (Python, PyTorch, Docker,
                                  # Apptainer, CUDA, ...) render as badges
    body: |        # optional; rendered on the project page (markdown + tables)
      What it does, in a paragraph or two.
```

### 3. (Optional) Fetch Publications from Google Scholar

You have two options for publications:

**Option A: Automatic (Recommended)**

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set your Google Scholar ID in `data/publications.yaml`:
   ```yaml
   google_scholar_id: "QGaRpqYAAAAJ"
   ```
   
   Find your ID in your Google Scholar profile URL:
   `https://scholar.google.com/citations?user=YOUR_ID_HERE`

3. Run the fetch script:
   ```bash
   python builder/fetch_publications.py
   ```

The script will automatically fetch all your publications from Google Scholar and update `data/publications.yaml`. You can run this periodically to keep your publications up to date.

**Option B: Manual Entry**

Just edit `data/publications.yaml` directly:
```yaml
papers:
  - date: "2025"
    title: "Your Paper Title"
    authors: "Author 1, Author 2, Your Name"
    venue: "Conference Name 2025"
    description: "Brief description"
    links:
      - name: "Paper"
        url: "https://arxiv.org/abs/xxxx.xxxxx"
      - name: "Code"
        url: "https://github.com/user/project"
```

### 4. (Optional) Add Your CV PDF
Add a PDF of your CV as `assets/img/cv.pdf` if you want the CV link to work.

## Building

The site is generated from `template.html` + the `data/*.yaml` files by the
builder package:

```bash
python -m builder        # writes index.html, sitemap.xml, resume.pdf, projects/
```

A tracked pre-commit hook rebuilds these artifacts automatically when a build
source changes. Enable it once per clone:

```bash
git config core.hooksPath .githooks
```

Blog pages are generated separately from org notes (not part of the main build):

```bash
python -m builder.build_blogs
```

## Customization

### Colors
The accent color is the `--accent-color` CSS variable (default `#0066cc`) in
`assets/css/style.css`, which also holds the light/dark theme values near the
top of the file.

### Layout
The site is fully responsive; edit `assets/css/style.css` to adjust spacing,
fonts, or layout.

### Adding/Removing Sections
`index.html` is generated - edit the placeholders in `template.html` and the
renderers in `builder/build_html.py`, then rebuild.

## Local Testing

**Important**: YAML loading requires a web server (can't just open the HTML file due to CORS).

```bash
# Python 3
python -m http.server 8000

# Then visit: http://localhost:8000
```

## Deployment to GitHub Pages

1. Push your changes to GitHub
2. Go to your repository Settings → Pages
3. Under "Source", select your branch (usually `main` or `master`)
4. Your site will be available at `https://yourusername.github.io`

## File Structure

```
├── index.html              # Generated site (built by `python -m builder`)
├── resume.pdf              # Generated résumé (kept at root)
├── builder/                # Static site builder (run: python -m builder)
│   ├── __main__.py         # Entry point
│   ├── build.py            # Orchestrates the build
│   ├── build_config.py     # Paths, author identity, link templates
│   ├── build_html.py       # HTML section renderers
│   ├── build_resume.py     # LaTeX → resume.pdf
│   ├── build_utils.py      # Shared helpers + YAML loading
│   └── fetch_publications.py  # Fetch from Google Scholar
├── requirements.txt        # Python dependencies
├── assets/                 # Static assets
│   ├── css/style.css       # All styling
│   ├── js/data.js          # Client-side JS (page navigation, etc.)
│   └── img/                # profile*.jpeg, cv.pdf, logos/, publications/
├── data/                   # git-crypt encrypted
│   ├── bio.yaml            # Bio information with social IDs
│   ├── education.yaml      # Education entries
│   ├── experience.yaml     # Work / internship entries
│   ├── research.yaml       # Research positions
│   ├── teaching.yaml       # Teaching / TA entries
│   ├── extracurricular.yaml# Honors & skills
│   ├── news.yaml           # News items
│   ├── publications.yaml   # Publications / papers
│   ├── blogs.yaml          # Blog post listings
│   └── works.yaml          # Open-source projects
└── README.md               # This file
```

## How It Works

1. When the page loads, `data.js` fetches all YAML files from the `data/` directory
2. The js-yaml library parses the YAML into JavaScript objects
3. Social links are automatically constructed from IDs using URL templates
4. The page content is dynamically populated using the data
5. All content updates are made by editing YAML files - no need to touch HTML!

## Google Scholar Integration Details

The `fetch_publications.py` script uses the free **scholarly** library to fetch publications:

- **Free**: No API keys or costs
- **Automatic**: Fetches all your publications from Google Scholar
- **Flexible**: You can still manually edit the YAML after fetching
- **Rate-limited**: Google Scholar may rate-limit, so the script includes delays

### Troubleshooting Google Scholar Fetch

If you encounter rate-limiting issues:
1. Wait a few hours and try again
2. Use a VPN to change your IP address
3. Manually add publications to `data/publications.yaml`

## License

See LICENSE.md for details.
