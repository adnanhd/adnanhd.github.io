// Load YAML data and populate the page
// This uses js-yaml library to parse YAML files

class DataLoader {
  constructor() {
    this.data = {
      bio: null,
      education: null,
      teaching: null,
      experience: null,
      research: null,
      extracurricular: null,
      news: null,
      publications: null,
      blogs: null,
      works: null,
    };

    // URL templates for social links
    this.urlTemplates = {
      email: (id) => `mailto:${id}`,
      github: (id) => `https://github.com/${id}`,
      linkedin: (id) => `https://linkedin.com/in/${id}`,
      google_scholar: (id) => `https://scholar.google.com/citations?user=${id}`,
      twitter: (id) => `https://twitter.com/${id}`,
      orcid: (id) => `https://orcid.org/${id}`,
      acm: (id) => `https://dl.acm.org/profile/${id}`,
      ieee: (id) => `https://ieeexplore.ieee.org/author/${id}`,
      dblp: (id) => `https://dblp.org/pid/${id}`,
      semantic_scholar: (id) => `https://www.semanticscholar.org/author/${id}`,
    };

    // Display names for social links
    this.linkNames = {
      email: "Email",
      github: "GitHub",
      linkedin: "LinkedIn",
      google_scholar: "Google Scholar",
      twitter: "Twitter",
      orcid: "ORCID",
      acm: "ACM DL",
      ieee: "IEEE Xplore",
      dblp: "DBLP",
      semantic_scholar: "Semantic Scholar",
    };

    // Icon classes for social links (Font Awesome and Academicons)
    this.linkIcons = {
      email: "fas fa-envelope",
      github: "fab fa-github",
      linkedin: "fab fa-linkedin",
      google_scholar: "ai ai-google-scholar",
      twitter: "fab fa-twitter",
      orcid: "ai ai-orcid",
      acm: "ai ai-acm",
      ieee: "ai ai-ieee",
      dblp: "ai ai-dblp",
      semantic_scholar: "ai ai-semantic-scholar",
    };
  }

  async loadYAML(url) {
    // Add cache busting for development
    const cacheBuster = new Date().getTime();
    const response = await fetch(`${url}?v=${cacheBuster}`);
    if (!response.ok) {
      throw new Error(`Failed to load ${url}: ${response.status}`);
    }
    const text = await response.text();
    return window.jsyaml.load(text);
  }

  async loadAll() {
    try {
      console.log("Loading YAML data...");
      this.data.bio = await this.loadYAML("data/bio.yaml");
      console.log("Loaded bio.yaml");
      this.data.education = await this.loadYAML("data/education.yaml");
      console.log("Loaded education.yaml");
      this.data.teaching = await this.loadYAML("data/teaching.yaml");
      console.log("Loaded teaching.yaml");
      this.data.experience = await this.loadYAML("data/experience.yaml");
      console.log("Loaded experience.yaml");
      this.data.research = await this.loadYAML("data/research.yaml");
      console.log("Loaded research.yaml");
      this.data.extracurricular = await this.loadYAML(
        "data/extracurricular.yaml",
      );
      console.log("Loaded extracurricular.yaml");
      this.data.news = await this.loadYAML("data/news.yaml");
      console.log("Loaded news.yaml");
      this.data.publications = await this.loadYAML("data/publications.yaml");
      console.log("Loaded publications.yaml");
      this.data.blogs = await this.loadYAML("data/blogs.yaml");
      console.log("Loaded blogs.yaml");
      this.data.works = await this.loadYAML("data/works.yaml");
      console.log("Loaded works.yaml");

      console.log("All data loaded, populating page...");
      this.populatePage();
      console.log("Page populated successfully!");
    } catch (error) {
      console.error("Error loading data:", error);
      alert(
        "Error loading website data. Please check the console for details.",
      );
    }
  }

  populatePage() {
    try {
      console.log("Starting populateBio...");
      this.populateBio();
      console.log("Starting populateResume...");
      this.populateResume();
      console.log("Starting populateNews...");
      this.populateNews();
      console.log("Starting populateTimeline...");
      this.populateTimeline();
      console.log("Finished populateTimeline");
      console.log("Starting populateBlogs...");
      this.populateBlogs();
      console.log("Finished populateBlogs");
      console.log("Starting populateAboutSections...");
      this.populateAboutSections();
      console.log("Finished populateAboutSections");
    } catch (error) {
      console.error("Error in populatePage:", error);
      throw error;
    }
  }

  populateTimeline() {
    const publications = this.data.publications;

    console.log("Publications data:", publications);

    if (!publications || !publications.papers) {
      console.log("No publications data");
      return;
    }

    console.log("Number of papers:", publications.papers.length);

    // Selected works on About page (fancy display with images)
    const selectedWorks = document.getElementById("selected-works");
    if (selectedWorks) {
      selectedWorks.innerHTML = "";
      const selected = publications.papers.filter((p) => p.selected);
      console.log("Selected works count:", selected.length);
      selected.forEach((paper) => {
        const card = this.createPublicationCard(paper);
        selectedWorks.appendChild(card);
      });
    }

    // Resume papers (papers marked with resume: true) - compact version
    const resumePapers = document.getElementById("resume-papers");
    if (resumePapers) {
      resumePapers.innerHTML = "";
      const resumeList = publications.papers.filter((p) => p.resume);
      console.log("Resume papers count:", resumeList.length);
      resumeList.forEach((paper) => {
        const card = this.createCompactPublicationCard(paper);
        resumePapers.appendChild(card);
      });
    }

    // Build unified timeline for News page
    this.buildUnifiedTimeline();
  }

  buildUnifiedTimeline() {
    const timelineContainer = document.getElementById("timeline-container");
    if (!timelineContainer) return;

    timelineContainer.innerHTML = "";

    // Collect all timeline events
    const events = [];

    // Add education (only if timelined flag is true)
    if (this.data.education && this.data.education.education) {
      this.data.education.education.forEach((edu) => {
        if (edu.timelined) {
          events.push({
            date: edu.start_date,
            type: "experience",
            title: edu.degree,
            organization: edu.institution,
            description: edu.description,
            endDate: edu.end_date,
          });
        }
      });
    }

    // Add experience (only if timelined flag is true)
    if (this.data.experience && this.data.experience.experience) {
      this.data.experience.experience.forEach((exp) => {
        if (exp.timelined) {
          events.push({
            date: exp.start_date,
            type: "experience",
            title: exp.position,
            organization: exp.company,
            description: exp.description,
            endDate: exp.end_date,
          });
        }
      });
    }

    // Add research internships (only if timelined flag is true)
    if (this.data.research && this.data.research.research) {
      this.data.research.research.forEach((res) => {
        if (res.timelined) {
          events.push({
            date: res.start_date,
            type: "experience",
            title: res.position,
            organization: res.company,
            description: res.description,
            endDate: res.end_date,
          });
        }
      });
    }

    // Add publications (only if timelined flag is true)
    if (this.data.publications && this.data.publications.papers) {
      this.data.publications.papers.forEach((paper) => {
        if (paper.timelined) {
          events.push({
            date: paper.date,
            type: "publication",
            title: paper.title,
            authors: paper.authors,
            venue: paper.venue_short || paper.venue,
            links: paper.links,
          });
        }
      });
    }

    // Sort events by date (newest first)
    events.sort((a, b) => {
      const dateA = this.parseDate(a.date);
      const dateB = this.parseDate(b.date);
      return dateB - dateA;
    });

    // Create timeline
    const timeline = document.createElement("div");
    timeline.className = "unified-timeline";

    events.forEach((event) => {
      const item = document.createElement("div");
      item.className = `timeline-row timeline-${event.type}`;

      if (event.type === "experience") {
        item.innerHTML = `
          <div class="timeline-left">
            <div class="timeline-date">${event.date}${event.endDate ? "<br>" + event.endDate : ""}</div>
          </div>
          <div class="timeline-center">
            <div class="timeline-marker"></div>
          </div>
          <div class="timeline-right">
            <div class="timeline-content-box">
              <h4>${event.title}</h4>
              <div class="timeline-org">${event.organization}</div>
            </div>
          </div>
        `;
      } else {
        // publication
        const linksHTML = event.links
          ? event.links
              .map(
                (link) =>
                  `<a href="${link.url}" target="_blank" class="timeline-link">${link.name}</a>`,
              )
              .join("")
          : "";

        item.innerHTML = `
          <div class="timeline-left">
            <div class="timeline-date">${event.date}</div>
          </div>
          <div class="timeline-center">
            <div class="timeline-marker"></div>
          </div>
          <div class="timeline-right">
            <div class="timeline-content-box">
              <h4>${event.title}</h4>
              <div class="timeline-authors">${event.authors}</div>
              <div class="timeline-venue"><em>${event.venue}</em></div>
              ${linksHTML ? `<div class="timeline-links">${linksHTML}</div>` : ""}
            </div>
          </div>
        `;
      }

      timeline.appendChild(item);
    });

    timelineContainer.appendChild(timeline);
  }

  parseDate(dateStr) {
    // Try to parse various date formats
    if (!dateStr) return new Date(0);

    // Handle "Present"
    if (dateStr.toLowerCase() === "present") return new Date();

    // Handle "Month YYYY" format
    const monthYear = dateStr.match(/^([A-Za-z]+)\s+(\d{4})$/);
    if (monthYear) {
      const months = {
        Jan: 0,
        Feb: 1,
        Mar: 2,
        Apr: 3,
        May: 4,
        Jun: 5,
        Jul: 6,
        Aug: 7,
        Sep: 8,
        Oct: 9,
        Nov: 10,
        Dec: 11,
        January: 0,
        February: 1,
        March: 2,
        April: 3,
        May: 4,
        June: 5,
        July: 6,
        August: 7,
        September: 8,
        October: 9,
        November: 10,
        December: 11,
        Spring: 2,
        Fall: 8,
      };
      const month = months[monthYear[1]] || 0;
      return new Date(parseInt(monthYear[2]), month);
    }

    // Handle just year
    const yearOnly = dateStr.match(/^(\d{4})$/);
    if (yearOnly) {
      return new Date(parseInt(yearOnly[1]), 0);
    }

    // Try standard date parsing
    return new Date(dateStr);
  }

  populateBlogs() {
    const blogs = this.data.blogs;
    const blogPosts = document.getElementById("blog-posts");

    if (!blogPosts) {
      console.log("Blog posts container not found");
      return;
    }

    blogPosts.innerHTML = "";

    if (!blogs || !blogs.blogs || blogs.blogs.length === 0) {
      const emptyMessage = document.createElement("p");
      emptyMessage.textContent = "No blog posts yet. Check back soon!";
      emptyMessage.style.color = "var(--text-secondary)";
      blogPosts.appendChild(emptyMessage);
      return;
    }

    blogs.blogs.forEach((blog) => {
      const blogItem = document.createElement("div");
      blogItem.className = "blog-item";

      const blogLink = document.createElement("a");
      blogLink.href = blog.path;
      blogLink.className = "blog-link";

      const blogTitle = document.createElement("h3");
      blogTitle.textContent = blog.title;

      const blogDate = document.createElement("span");
      blogDate.className = "blog-date";
      blogDate.textContent = blog.date;

      if (blog.description) {
        const blogDesc = document.createElement("p");
        blogDesc.textContent = blog.description;
        blogLink.appendChild(blogTitle);
        blogLink.appendChild(blogDate);
        blogLink.appendChild(blogDesc);
      } else {
        blogLink.appendChild(blogTitle);
        blogLink.appendChild(blogDate);
      }

      blogItem.appendChild(blogLink);
      blogPosts.appendChild(blogItem);
    });
  }

  createCompactPublicationCard(paper) {
    const card = document.createElement("div");
    card.className = "publication-item-compact";

    // APA-style reference: Authors. (Year). Title. Venue.
    const reference = document.createElement("div");
    reference.className = "pub-compact-reference";

    // Authors with highlighting
    const authorText = paper.authors.replace(
      /Adnan Harun Dogan|Adnan Harun Doğan/g,
      "<strong>Adnan Harun Dogan</strong>",
    );

    // Build APA-style citation
    let citation = authorText;

    if (paper.date) {
      citation += ` (${paper.date}).`;
    }

    citation += ` ${paper.title}.`;

    if (paper.venue_link && paper.venue_short) {
      citation += ` <em><a href="${paper.venue_link}" target="_blank" style="color: var(--accent-color); text-decoration: none;">${paper.venue_short}</a></em>.`;
    } else if (paper.venue) {
      citation += ` <em>${paper.venue}</em>.`;
    }

    reference.innerHTML = citation;
    card.appendChild(reference);

    if (paper.links && paper.links.length > 0) {
      const linksDiv = document.createElement("div");
      linksDiv.className = "publication-links";

      paper.links.forEach((link) => {
        const a = document.createElement("a");
        a.href = link.url;
        a.className = "pub-link";
        a.textContent = link.name;
        a.target = "_blank";
        linksDiv.appendChild(a);
      });

      card.appendChild(linksDiv);
    }

    return card;
  }

  createPublicationCard(paper) {
    const card = document.createElement("div");
    card.className = "publication-item";

    // Left side: venue tag + image
    const left = document.createElement("div");
    left.className = "publication-left";

    const venueTag = document.createElement("div");
    venueTag.className = "publication-venue-tag";

    if (paper.venue_link) {
      const venueLink = document.createElement("a");
      venueLink.href = paper.venue_link;
      venueLink.target = "_blank";
      venueLink.textContent = paper.venue_short || paper.venue || "Publication";
      venueLink.style.color = "inherit";
      venueLink.style.textDecoration = "none";
      venueTag.appendChild(venueLink);
    } else {
      venueTag.textContent = paper.venue_short || paper.venue || "Publication";
    }

    left.appendChild(venueTag);

    if (paper.image) {
      const imageDiv = document.createElement("div");
      imageDiv.className = "publication-image";
      const img = document.createElement("img");
      img.src = paper.image;
      img.alt = paper.title;
      imageDiv.appendChild(img);
      left.appendChild(imageDiv);
    }

    // Right side: title, authors, venue, links
    const content = document.createElement("div");
    content.className = "publication-content";

    const title = document.createElement("div");
    title.className = "publication-title";
    title.textContent = paper.title;
    content.appendChild(title);

    const authors = document.createElement("div");
    authors.className = "publication-authors";
    const authorText = paper.authors.replace(
      /Adnan Harun Dogan|Adnan Harun Doğan/g,
      '<span class="author-me">Adnan Harun Dogan</span>',
    );
    authors.innerHTML = authorText;
    content.appendChild(authors);

    const venue = document.createElement("div");
    venue.className = "publication-venue";
    venue.textContent = `${paper.venue}${paper.date ? ", " + paper.date : ""}`;
    content.appendChild(venue);

    if (paper.links && paper.links.length > 0) {
      const linksDiv = document.createElement("div");
      linksDiv.className = "publication-links";

      paper.links.forEach((link) => {
        const a = document.createElement("a");
        a.href = link.url;
        a.className = "pub-link";
        a.textContent = link.name;
        a.target = "_blank";
        linksDiv.appendChild(a);
      });

      content.appendChild(linksDiv);
    }

    card.appendChild(left);
    card.appendChild(content);

    return card;
  }
  populateBio() {
    const bio = this.data.bio;
    if (!bio) {
      console.error("Bio data not loaded");
      return;
    }

    // Update sidebar info
    const sidebarName = document.querySelector(".sidebar-name");
    const sidebarTitle = document.querySelector(".sidebar-title");
    const sidebarAffiliation = document.querySelector(".sidebar-affiliation");

    if (sidebarName) sidebarName.textContent = bio.name;
    if (sidebarTitle) sidebarTitle.textContent = bio.title;
    if (sidebarAffiliation) sidebarAffiliation.textContent = bio.affiliation;

    // Update profile image
    document.querySelector(".bio-image img").src = bio.profile_image;
    document.querySelector(".bio-image img").alt = bio.name;

    // Update short bio in left sidebar
    if (bio.short_bio) {
      document.querySelector(".bio-short").textContent = bio.short_bio;
    }

    // Update Twitter timeline if twitter username exists
    if (bio.social && bio.social.twitter) {
      const twitterLink = document.querySelector(".twitter-timeline");
      if (twitterLink) {
        twitterLink.href = `https://twitter.com/${bio.social.twitter}?ref_src=twsrc%5Etfw`;
        twitterLink.textContent = `Tweets by ${bio.social.twitter}`;

        // Set theme based on user preference
        const isDark =
          window.matchMedia &&
          window.matchMedia("(prefers-color-scheme: dark)").matches;
        twitterLink.setAttribute("data-theme", isDark ? "dark" : "light");
      }
    }

    // Update bio description (allow HTML for links)
    const bioDesc = document.querySelector(".bio-description");
    bioDesc.innerHTML = "";
    const paragraphs = bio.bio.split("\n\n");
    paragraphs.forEach((para) => {
      if (para.trim()) {
        const p = document.createElement("p");
        p.innerHTML = para.trim(); // Use innerHTML to render HTML links
        bioDesc.appendChild(p);
      }
    });

    // Update links - construct from IDs
    const linksContainer = document.querySelector(".links");
    linksContainer.innerHTML = "";

    // Add social links from IDs
    if (bio.social) {
      Object.keys(bio.social).forEach((platform) => {
        const id = bio.social[platform];
        if (id && id.trim()) {
          // Only add if ID is not empty
          const a = document.createElement("a");
          a.href = this.urlTemplates[platform](id);
          a.className = "social-link";
          a.title = this.linkNames[platform];
          a.setAttribute("aria-label", this.linkNames[platform]);

          // Create icon element
          const icon = document.createElement("i");
          icon.className = this.linkIcons[platform];
          a.appendChild(icon);

          // Create label element
          const label = document.createElement("span");
          label.className = "social-label";
          label.textContent = this.linkNames[platform];
          a.appendChild(label);

          if (!a.href.startsWith("mailto:")) {
            a.target = "_blank";
          }
          linksContainer.appendChild(a);
        }
      });
    }

    // Add custom links
    if (bio.custom_links) {
      bio.custom_links.forEach((link) => {
        const a = document.createElement("a");
        a.href = link.url;
        a.textContent = link.name;
        if (link.url.startsWith("http")) {
          a.target = "_blank";
        }
        linksContainer.appendChild(a);
      });
    }

    // Update page title
    document.title = bio.name;
  }

  populateResume() {
    // Education section
    const educationList = document.getElementById("education-list");
    if (educationList && this.data.education && this.data.education.education) {
      educationList.innerHTML = "";
      this.data.education.education.forEach((edu) => {
        const item = this.createResumeItemWithLinks(
          edu.degree,
          edu.institution,
          `${edu.start_date} - ${edu.end_date}`,
          edu.description,
          edu.logo,
          edu.links,
          edu.logo_link,
          edu.commitment,
          edu.advisor,
          edu.bullets,
        );
        educationList.appendChild(item);
      });
    }

    // Teaching Experience section
    const teachingList = document.getElementById("teaching-list");
    console.log("Teaching list element:", teachingList);
    console.log("Teaching data:", this.data.teaching);
    if (teachingList && this.data.teaching && this.data.teaching.teaching) {
      console.log("Teaching entries:", this.data.teaching.teaching.length);
      teachingList.innerHTML = "";
      this.data.teaching.teaching.forEach((teach) => {
        const item = this.createResumeItemWithLinks(
          teach.position,
          teach.company,
          `${teach.start_date} - ${teach.end_date}`,
          teach.description,
          teach.logo,
          teach.links,
          teach.logo_link,
          teach.commitment,
          teach.advisor,
          teach.bullets,
        );
        teachingList.appendChild(item);
      });
    } else {
      console.log("Teaching section not populated - missing element or data");
    }

    // Experience section
    const experienceList = document.getElementById("experience-list");
    if (
      experienceList &&
      this.data.experience &&
      this.data.experience.experience
    ) {
      experienceList.innerHTML = "";
      this.data.experience.experience.forEach((exp) => {
        const item = this.createResumeItemWithLinks(
          exp.position,
          exp.company,
          `${exp.start_date} - ${exp.end_date}`,
          exp.description,
          exp.logo,
          exp.links,
          exp.logo_link,
          exp.commitment,
          exp.advisor,
          exp.bullets,
        );
        experienceList.appendChild(item);
      });
    }

    // Research Internships section
    const researchList = document.getElementById("research-list");
    if (researchList && this.data.research && this.data.research.research) {
      researchList.innerHTML = "";
      this.data.research.research.forEach((res) => {
        const item = this.createResumeItemWithLinks(
          res.position,
          res.company,
          `${res.start_date} - ${res.end_date}`,
          res.description,
          res.logo,
          res.links,
          res.logo_link,
          res.commitment,
          res.advisor,
          res.bullets,
        );
        researchList.appendChild(item);
      });
    }

    // Honors section
    const honorsList = document.getElementById("honors-list");
    if (
      honorsList &&
      this.data.extracurricular &&
      this.data.extracurricular.honors
    ) {
      honorsList.innerHTML = "";
      this.data.extracurricular.honors.forEach((honor) => {
        const item = this.createResumeItemWithLinks(
          honor.title,
          honor.organization,
          honor.date,
          honor.description,
          honor.logo,
          honor.links,
          honor.logo_link,
          honor.commitment,
          honor.advisor,
          honor.bullets,
        );
        honorsList.appendChild(item);
      });
    }
  }

  createItemsContainer(section) {
    const container = document.createElement("div");
    container.className = "resume-items";
    section.appendChild(container);
    return container;
  }

  createResumeItem(title, subtitle, date, description, logo) {
    const item = document.createElement("div");
    item.className = "resume-item";

    // Add logo if provided
    if (logo) {
      const logoDiv = document.createElement("div");
      logoDiv.className = "resume-logo";
      const img = document.createElement("img");
      img.src = logo;
      img.alt = subtitle;
      logoDiv.appendChild(img);
      item.appendChild(logoDiv);
    }

    // Create details container
    const details = document.createElement("div");
    details.className = "resume-details";

    const header = document.createElement("div");
    header.className = "resume-header";
    header.innerHTML = `
            <strong>${title}</strong>
            <span class="date">${date}</span>
        `;

    const subheader = document.createElement("div");
    subheader.className = "resume-subheader";
    subheader.textContent = subtitle;

    // Add commitment if provided
    if (commitment) {
      const commitmentDiv = document.createElement("div");
      commitmentDiv.className = "resume-commitment";
      commitmentDiv.textContent = commitment;
      details.appendChild(header);
      details.appendChild(subheader);
      details.appendChild(commitmentDiv);
    } else {
      details.appendChild(header);
      details.appendChild(subheader);
    }

    const desc = document.createElement("p");
    desc.textContent = description;

    details.appendChild(desc);

    item.appendChild(details);

    return item;
  }

  createResumeItemWithLinks(
    title,
    subtitle,
    date,
    description,
    logo,
    links,
    logo_link,
    commitment,
    advisor,
    bullets,
  ) {
    const item = document.createElement("div");
    item.className = "resume-item";

    // Add logo if provided (clickable if logo_link exists)
    if (logo) {
      const logoDiv = document.createElement("div");
      logoDiv.className = "resume-logo";

      if (logo_link) {
        const logoLink = document.createElement("a");
        logoLink.href = logo_link;
        logoLink.target = "_blank";
        const img = document.createElement("img");
        img.src = logo;
        img.alt = subtitle;
        logoLink.appendChild(img);
        logoDiv.appendChild(logoLink);
      } else {
        const img = document.createElement("img");
        img.src = logo;
        img.alt = subtitle;
        logoDiv.appendChild(img);
      }

      item.appendChild(logoDiv);
    }

    // Create details container
    const details = document.createElement("div");
    details.className = "resume-details";

    const header = document.createElement("div");
    header.className = "resume-header";
    header.innerHTML = `
            <strong>${title}</strong>
            <span class="date">${date}</span>
        `;

    const subheader = document.createElement("div");
    subheader.className = "resume-subheader";

    const subheaderText = document.createElement("span");
    subheaderText.textContent = subtitle;
    subheader.appendChild(subheaderText);

    // Add commitment on the same line if provided
    if (commitment && commitment.trim()) {
      const commitmentSpan = document.createElement("span");
      commitmentSpan.className = "resume-commitment";
      commitmentSpan.textContent = commitment;
      subheader.appendChild(commitmentSpan);
    }

    details.appendChild(header);
    details.appendChild(subheader);

    // Add advisor if provided
    if (advisor && advisor.trim()) {
      const advisorDiv = document.createElement("div");
      advisorDiv.className = "resume-advisor";
      advisorDiv.innerHTML = `<strong>Advisor:</strong> ${advisor}`;
      details.appendChild(advisorDiv);
    }

    // Add description
    const desc = document.createElement("p");
    desc.textContent = description;
    details.appendChild(desc);

    // Add bullets if provided
    if (bullets && bullets.length > 0) {
      const bulletList = document.createElement("ul");
      bulletList.className = "resume-bullets";
      bullets.forEach((bullet) => {
        const li = document.createElement("li");

        // Check if this is a course code (e.g., "CENG 315 - Algorithms")
        const courseMatch = bullet.match(/^(CENG \d+)\s*-\s*(.+)$/);
        if (courseMatch) {
          const courseCode = courseMatch[1];
          const courseName = courseMatch[2];
          const courseNumber = courseCode.replace("CENG ", "");
          const catalogUrl = `https://catalog.metu.edu.tr/course.php?course_code=5710${courseNumber}`;

          const link = document.createElement("a");
          link.href = catalogUrl;
          link.target = "_blank";
          link.textContent = courseCode;
          link.style.color = "var(--accent-color)";
          link.style.textDecoration = "none";

          li.appendChild(link);
          li.appendChild(document.createTextNode(` - ${courseName}`));
        } else {
          li.textContent = bullet;
        }

        bulletList.appendChild(li);
      });
      details.appendChild(bulletList);
    }

    // Add links if provided (rectangular boxes like publications)
    if (links && links.length > 0) {
      const linksDiv = document.createElement("div");
      linksDiv.className = "publication-links";

      links.forEach((link) => {
        const a = document.createElement("a");
        a.href = link.url;
        a.className = "pub-link";
        a.textContent = link.name;
        a.target = "_blank";
        linksDiv.appendChild(a);
      });

      details.appendChild(linksDiv);
    }

    item.appendChild(details);

    return item;
  }

  populateNews() {
    const news = this.data.news;
    const newsList = document.querySelector(".news-list");
    newsList.innerHTML = "";

    news.items.forEach((item) => {
      const li = document.createElement("li");

      const dateSpan = document.createElement("span");
      dateSpan.className = "news-date";
      dateSpan.textContent = `[${item.date}]`;

      const contentSpan = document.createElement("span");
      contentSpan.className = "news-content";

      if (item.link) {
        const a = document.createElement("a");
        a.href = item.link;
        a.textContent = item.content;
        a.target = "_blank";
        contentSpan.appendChild(a);
      } else {
        contentSpan.textContent = item.content;
      }

      li.appendChild(dateSpan);
      li.appendChild(document.createTextNode(" "));
      li.appendChild(contentSpan);
      newsList.appendChild(li);
    });
  }

  populateAboutSections() {
    // Selected blogs on About page
    const selectedBlogs = document.getElementById("selected-blogs");
    if (selectedBlogs && this.data.blogs && this.data.blogs.blogs) {
      selectedBlogs.innerHTML = "";
      const selected = this.data.blogs.blogs.filter((b) => b.selected);

      if (selected.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.textContent = "No selected blogs yet.";
        emptyMessage.style.color = "var(--text-secondary)";
        selectedBlogs.appendChild(emptyMessage);
      } else {
        selected.forEach((blog) => {
          const blogItem = document.createElement("div");
          blogItem.className = "blog-item";
          const blogLink = document.createElement("a");
          blogLink.href = blog.path;
          const blogTitle = document.createElement("h3");
          blogTitle.textContent = blog.title;
          blogLink.appendChild(blogTitle);
          if (blog.description) {
            const blogDesc = document.createElement("p");
            blogDesc.textContent = blog.description;
            blogLink.appendChild(blogDesc);
          }
          blogItem.appendChild(blogLink);
          selectedBlogs.appendChild(blogItem);
        });
      }
    }

    // Selected works on About page
    const selectedRepos = document.getElementById("selected-repos");
    if (selectedRepos && this.data.works && this.data.works.works) {
      selectedRepos.innerHTML = "";

      if (this.data.works.works.length === 0) {
        const emptyMessage = document.createElement("p");
        emptyMessage.textContent = "No selected works yet.";
        emptyMessage.style.color = "var(--text-secondary)";
        selectedRepos.appendChild(emptyMessage);
      } else {
        this.data.works.works.forEach((work) => {
          const workItem = document.createElement("div");
          workItem.className = "work-item";
          const workLink = document.createElement("a");
          workLink.href = work.url;
          workLink.target = "_blank";
          const workTitle = document.createElement("h3");
          workTitle.textContent = work.title;
          workLink.appendChild(workTitle);
          if (work.description) {
            const workDesc = document.createElement("p");
            workDesc.textContent = work.description;
            workLink.appendChild(workDesc);
          }
          if (work.tags && work.tags.length > 0) {
            const tagsDiv = document.createElement("div");
            tagsDiv.className = "work-tags";
            work.tags.forEach((tag) => {
              const tagSpan = document.createElement("span");
              tagSpan.className = "work-tag";
              tagSpan.textContent = tag;
              tagsDiv.appendChild(tagSpan);
            });
            workLink.appendChild(tagsDiv);
          }
          workItem.appendChild(workLink);
          selectedRepos.appendChild(workItem);
        });
      }
    }
  }
}

// Theme management
function initTheme() {
  const themeToggle = document.getElementById("theme-toggle");
  const htmlElement = document.documentElement;

  // Check for saved theme preference or default to system preference
  const savedTheme = localStorage.getItem("theme");

  if (savedTheme) {
    htmlElement.setAttribute("data-theme", savedTheme);
  } else {
    // Check system preference
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches;
    if (prefersDark) {
      htmlElement.setAttribute("data-theme", "dark");
    }
  }

  // Toggle theme on button click
  themeToggle.addEventListener("click", () => {
    const currentTheme = htmlElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    htmlElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  });

  // Listen for system theme changes (only if no manual override)
  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", (e) => {
      if (!localStorage.getItem("theme")) {
        htmlElement.setAttribute("data-theme", e.matches ? "dark" : "light");
      }
    });
}

// Initialize when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  const loader = new DataLoader();
  loader.loadAll();
});
