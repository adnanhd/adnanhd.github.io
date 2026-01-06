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

#### `data/bio.yaml`
```yaml
social:
  email: "your.email@example.com"
  github: "adnanhd"
  linkedin: "yourprofile"
  google_scholar: "QGaRpqYAAAAJ"  # Your Google Scholar ID
  twitter: ""  # Optional
  orcid: ""    # Optional
```

Just provide the IDs/usernames - full URLs are generated automatically!

Supported platforms:
- **email**: your email address
- **github**: GitHub username
- **linkedin**: LinkedIn username (from profile URL)
- **google_scholar**: Google Scholar ID (from your profile URL)
- **acm**: ACM Digital Library profile ID
- **ieee**: IEEE Xplore author ID
- **dblp**: DBLP author ID (e.g., "301/3453")
- **semantic_scholar**: Semantic Scholar author ID
- **twitter**: Twitter/X handle
- **orcid**: ORCID ID

You can also add custom links:
```yaml
custom_links:
  - name: "CV"
    url: "cv.pdf"
  - name: "Blog"
    url: "https://yourblog.com"
```

#### `data/cv.yaml`
- Education entries
- Work experience entries
- Timeline entries for the left column (education & internships)

#### `data/news.yaml`
- News items with dates
- Optional links for news items

#### `data/publications.yaml`
- Publication entries with title, authors, venue, description
- Links (paper, code, project page, etc.)
- These appear in the right timeline column

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
   python fetch_publications.py
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
Add a PDF of your CV as `cv.pdf` in the root directory if you want the CV link to work.

## Customization

### Colors
The main accent color (`#3498db` - blue) is defined in `style.css`. Search and replace to change:
```css
/* Find: #3498db */
/* Replace with your preferred color (e.g., #e74c3c for red) */
```

### Layout
The site is fully responsive. Edit `style.css` to adjust spacing, fonts, or layout as needed.

### Adding/Removing Sections
Edit `index.html` to add or remove sections. The JavaScript in `data.js` automatically populates content from YAML files.

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
├── index.html              # Main HTML structure
├── style.css               # All styling
├── data.js                 # JavaScript to load YAML and populate page
├── fetch_publications.py   # Script to fetch from Google Scholar
├── requirements.txt        # Python dependencies
├── profile.jpeg            # Your profile picture
├── cv.pdf                  # (Optional) Your CV PDF
├── data/
│   ├── bio.yaml            # Bio information with social IDs
│   ├── cv.yaml             # Education & experience
│   ├── news.yaml           # News items
│   └── publications.yaml   # Publications/papers
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
