# IBM Consulting Marketing Intelligence Dashboard

A multi-tab AI-powered marketing intelligence dashboard built for IBM Consulting's marketing and leadership teams. Upload any number of analyst reports, white papers, competitor publications, or IBM research documents — and get a full 9-tab marketing brief in minutes.

---

## Features

| Tab | Output |
|---|---|
| **1 – Executive Summary** | Top 10 findings, strategic implications, risks, recommended actions |
| **2 – Blog Content Opportunities** | Ready-to-brief blog ideas with titles, stats, quotes, CTAs |
| **3 – IBM Consulting Priorities** | Alignment to Cybersecurity and Autonomous Security priorities |
| **4 – Focus Areas & Meeting Agendas** | Strategic focus areas + structured meeting agenda templates |
| **5 – Social Media Content Hub** | LinkedIn posts (3 types), carousels, polls, infographic concepts |
| **6 – Email Generator** | IBM-compliant emails for clients, prospects, internal stakeholders |
| **7 – Industry Direction & Outlook** | 12/24/36-month outlook with APAC-specific analysis |
| **8 – Industry & Technology Trends** | Ranked trends with business opportunities and marketing implications |
| **9 – Competitive Intelligence** | Competitor assessment vs IBM with positioning recommendations |
| **Final Deliverable** | Top 5: opportunities, threats, marketing actions, campaigns, talking points |

---

## Supported File Types

- PDF (`.pdf`)
- Word Documents (`.docx`)
- PowerPoint Presentations (`.pptx`)
- Plain Text (`.txt`, `.md`)
- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)

---

## Setup

### 1. Clone / Navigate to project

```bash
cd ibm-marketing-intelligence
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your ICA API key

Your `.env` file is already configured. To change keys, edit `.env`:

```
ICA_API_KEY=your-key-here
ICA_BASE_URL=https://api.nextgen-beta.ica.ibm.com/ica/v1
ICA_MODEL=claude-sonnet-4-5
```

### 5. Run the dashboard

```bash
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

---

## Usage

1. **Upload documents** — drag & drop files in the sidebar (upload as many as needed)
2. **Select tabs** — choose which tabs to generate (or tick "Select All")
3. **Click Run Analysis** — the agent processes all documents and generates the dashboard
4. **Download outputs** — download individual tabs or the full report as Markdown

---

## Project Structure

```
ibm-marketing-intelligence/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env                        # ICA API credentials (not committed to git)
├── .env.template               # Template for sharing credentials setup
├── utils/
│   ├── file_parser.py          # Extracts text from PDF, DOCX, PPTX, etc.
│   ├── ica_client.py           # ICA API wrapper (OpenAI-compatible)
│   └── prompt_engine.py        # Per-tab system/user prompts
└── tabs/                       # Reserved for future tab module expansion
```

---

## Notes

- All outputs are AI-generated and **require human review** before external use.
- IBM Consulting Confidential — do not share outputs without appropriate review.
- Large documents are automatically truncated to fit model context limits.
- If a tab fails, check the error details expanded panel for API diagnostics.
