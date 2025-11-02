# 📁 Complete File Structure Explanation

This document explains every file in the project, what it does, and how they all work together.

---

## 🗂️ Project Structure Overview

```
WEB_SCRAPER/
│
├── 📄 main.py                      # ⭐ START HERE - Entry point
├── 📄 requirements.txt             # Dependencies list
├── 📄 .gitignore                   # Git ignore rules
│
├── 📂 src/                         # Main source code directory
│   ├── __init__.py                 # Makes src a Python package
│   ├── jira_client.py              # 🔌 API communication layer
│   ├── state_manager.py            # 💾 State persistence layer
│   ├── data_transformer.py         # 🔄 Data transformation layer
│   └── scraper.py                  # 🎯 Main orchestration logic
│
├── 📂 state/                       # Auto-generated: stores progress
│   └── scrape_state.json           # Current scraping state
│
├── 📂 venv/                        # Virtual environment (auto-created)
│
├── 📄 jira_dataset.jsonl           # Output file (auto-generated)
│
├── 📄 README.md                    # Main documentation
├── 📄 QUICKSTART.md                # Quick reference guide
│
└── 🧪 Test & Utility Files
    ├── setup.py                    # Setup verification script
    ├── test_api_connection.py      # API connection test
    ├── test_specific_issue.py      # Single issue test
    └── example_usage.py            # Usage examples
```

---

## 📋 Detailed File Explanations

### 🎯 **1. main.py** - The Entry Point

**Purpose**: Main entry point when you run the scraper from command line

**What it does**:
- Parses command-line arguments (`--projects`, `--output`, etc.)
- Sets up logging (saves to `scraper.log` and prints to console)
- Creates a `JiraScraper` instance
- Handles user commands (reset, start scraping)
- Prints summary statistics when done

**When it runs**: First file executed when you type `python main.py`

**Key Functions**:
```python
def main():
    # 1. Parse command line arguments
    # 2. Create JiraScraper instance
    # 3. Call scraper.scrape_all()
    # 4. Print results
```

**Example Usage**:
```bash
python main.py --projects SPARK HADOOP --delay 1.5
```

---

### 🔌 **2. src/jira_client.py** - API Communication Layer

**Purpose**: Handles all HTTP requests to Apache Jira REST API

**What it contains**:
- `JiraClient` class - Main API client
- Methods to fetch issues, comments, project info
- Error handling (429 rate limits, 5xx errors, timeouts)
- Retry logic with exponential backoff
- Rate limiting delays

**Key Methods**:
- `get_issue(issue_key)` - Fetch single issue details
- `search_issues(project, start_at, max_results)` - Search with pagination
- `get_issue_comments(issue_key)` - Get comments for an issue
- `get_project_info(project_key)` - Get project metadata
- `_make_request()` - Internal method with retry logic

**How it handles errors**:
- HTTP 429 (Rate Limiting) → Waits and retries
- HTTP 5xx (Server Errors) → Exponential backoff retry
- Timeout → Retries with increasing delays
- Connection Error → Retries up to 5 times

**Example Flow**:
```
User calls → search_issues('SPARK', start_at=0)
           ↓
    _make_request('GET', 'search', params={...})
           ↓
    Makes HTTP request to Jira API
           ↓
    If error → Retry with backoff
           ↓
    Returns JSON response
```

---

### 💾 **3. src/state_manager.py** - State Persistence Layer

**Purpose**: Tracks scraping progress so you can resume after interruptions

**What it does**:
- Saves which issues have been processed
- Stores pagination position (start_at index)
- Allows resuming from last checkpoint
- Manages state file: `state/scrape_state.json`

**Key Methods**:
- `get_processed_issues(project)` - Get set of already-scraped issue keys
- `mark_issue_processed(project, issue_key)` - Mark issue as done
- `update_project_progress(project, start_at)` - Save pagination position
- `save_state()` - Write state to disk
- `reset_project(project)` - Clear state for a project

**State File Structure**:
```json
{
  "projects": {
    "SPARK": {
      "start_at": 150,           // Current pagination position
      "last_issue_key": "SPARK-12345"
    }
  },
  "processed_issues": {
    "SPARK": ["SPARK-1", "SPARK-2", ...],  // Already scraped
    "HADOOP": ["HADOOP-1", ...]
  },
  "last_updated": "2025-01-01T12:00:00"
}
```

**Why it's important**: 
- If scraping crashes, you can resume without re-scraping everything
- Tracks duplicates to avoid processing same issue twice

---

### 🔄 **4. src/data_transformer.py** - Data Transformation Layer

**Purpose**: Converts raw Jira API responses into clean JSONL format for LLM training

**What it does**:
- Extracts plain text from HTML/structured fields
- Formats timestamps to readable dates
- Extracts labels, components, comments
- Generates derived tasks (summarization, classification, Q&A)
- Writes to JSONL file (one JSON object per line)

**Key Methods**:
- `extract_text_content(field)` - Converts HTML/structured data to plain text
- `extract_comments(issue, comments_data)` - Extracts and formats comments
- `transform_issue(issue, comments_data)` - Main transformation method
- `create_derived_tasks(issue_data)` - Generates LLM training tasks
- `write_jsonl(data, output_file)` - Writes to output file

**Transformation Flow**:
```
Raw Jira API JSON
     ↓
Extract fields (title, description, status, etc.)
     ↓
Clean HTML from description/comments
     ↓
Format timestamps
     ↓
Generate derived tasks
     ↓
Clean JSONL format
```

**Output Format**:
```json
{
  "issue_key": "SPARK-12345",
  "title": "Issue title",
  "description": "Clean plain text description",
  "status": "Resolved",
  "comments": [...],
  "derived_tasks": {
    "summarization": {...},
    "classification": {...},
    "qa_generation": {...}
  }
}
```

---

### 🎯 **5. src/scraper.py** - Main Orchestration Logic

**Purpose**: Coordinates everything - the "conductor" of the orchestra

**What it contains**:
- `JiraScraper` class - Main scraper that ties everything together
- Orchestrates API calls, state management, and data transformation
- Handles pagination across multiple projects
- Manages batches and saves progress periodically

**Key Methods**:
- `__init__()` - Initializes all components (client, state, transformer)
- `scrape_project(project)` - Scrapes one project with pagination
- `scrape_all()` - Scrapes all configured projects
- `reset_project(project)` - Resets state for a project

**Execution Flow in `scrape_project()`**:
```
1. Check state for already-processed issues
2. Get total issue count from API
3. Loop through pages (pagination):
   a. Fetch page of issues from API
   b. For each issue:
      - Check if already processed → skip
      - Fetch issue details + comments
      - Transform to JSONL format
      - Add to batch
      - Mark as processed
   c. Every N issues (batch_size):
      - Write batch to JSONL file
      - Save state to disk
4. Return total scraped count
```

**How Components Work Together**:
```python
JiraScraper
    ├── Uses JiraClient → Makes API calls
    ├── Uses StateManager → Tracks progress
    └── Uses DataTransformer → Converts data
```

---

### 📦 **6. src/__init__.py** - Package Initializer

**Purpose**: Makes `src` directory a Python package

**What it does**: 
- Allows importing like: `from src.jira_client import JiraClient`
- Currently just contains a comment, but required for package structure

---

## 🔄 Complete Execution Flow

Here's what happens when you run `python main.py`:

### Step-by-Step Flow:

```
1. main.py starts
   ↓
2. Parse command-line arguments
   ↓
3. Set up logging
   ↓
4. Create JiraScraper instance:
   ├── Creates JiraClient (API handler)
   ├── Creates StateManager (loads saved state)
   └── Creates DataTransformer (data converter)
   ↓
5. Check for reset commands (if --reset flag)
   ↓
6. Call scraper.scrape_all()
   ↓
7. For each project:
   ├── scraper.scrape_project(project)
   │   ├── Check StateManager: Which issues already processed?
   │   ├── Call JiraClient.search_issues() → Get page of issues
   │   │   └── JiraClient handles retries, rate limits, errors
   │   ├── For each issue in page:
   │   │   ├── Call JiraClient.get_issue() → Get details
   │   │   ├── Call JiraClient.get_issue_comments() → Get comments
   │   │   ├── Call DataTransformer.transform_issue() → Convert to JSONL
   │   │   ├── StateManager.mark_issue_processed() → Track progress
   │   │   └── Add to batch
   │   ├── Every batch_size issues:
   │   │   ├── DataTransformer.write_jsonl() → Save to file
   │   │   └── StateManager.save_state() → Save progress
   │   └── Continue pagination until done
   ↓
8. Print summary statistics
   ↓
9. Done! ✅
```

### Visual Flow Diagram:

```
┌─────────────┐
│   main.py   │  ← You run this
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  JiraScraper     │  ← Orchestrates everything
│  (scraper.py)    │
└──┬───────────┬───┘
   │           │
   ▼           ▼
┌──────────┐ ┌──────────────────┐
│JiraClient│ │  StateManager    │
│(API calls)│ │(Progress tracking)│
└────┬─────┘ └──────────┬───────┘
     │                  │
     │                  ▼
     │         ┌─────────────────┐
     │         │ scrape_state.json│
     │         └─────────────────┘
     │
     ▼
┌────────────────────┐
│ DataTransformer    │
│ (Convert to JSONL) │
└──────┬─────────────┘
       │
       ▼
┌──────────────────┐
│ jira_dataset.jsonl│ ← Final output
└──────────────────┘
```

---

## 📁 Supporting Files

### **requirements.txt**
- Lists all Python dependencies
- Used by `pip install -r requirements.txt`
- Contains: `requests`, `python-dateutil`, `tqdm`

### **.gitignore**
- Tells Git which files to ignore
- Ignores: `__pycache__/`, `venv/`, `*.jsonl`, `state/`, etc.

### **README.md**
- Comprehensive documentation
- Setup instructions, architecture, edge cases

### **QUICKSTART.md**
- Quick reference guide
- Basic usage examples

### **setup.py**
- Verifies installation
- Checks Python version, dependencies, project structure
- Run: `python setup.py`

### **test_api_connection.py**
- Tests if you can connect to Apache Jira API
- Useful for troubleshooting
- Run: `python test_api_connection.py`

### **test_specific_issue.py**
- Tests fetching a single issue
- Shows raw API response and transformed output
- Useful for debugging

### **example_usage.py**
- Shows programmatic usage examples
- How to use scraper in your own code

---

## 🔗 How Files Depend on Each Other

### Dependency Graph:

```
main.py
  └──→ scraper.py (JiraScraper class)
          ├──→ jira_client.py (JiraClient class)
          ├──→ state_manager.py (StateManager class)
          └──→ data_transformer.py (DataTransformer class)
```

### Import Chain:

```python
# main.py imports:
from src.scraper import JiraScraper

# scraper.py imports:
from .jira_client import JiraClient
from .state_manager import StateManager
from .data_transformer import DataTransformer

# No circular dependencies! ✅
```

---

## 📊 Data Flow Example

Let's trace a single issue through the system:

### Example: Fetching issue "SPARK-12345"

1. **main.py**: User runs `python main.py --projects SPARK`
2. **scraper.py**: `scrape_project('SPARK')` called
3. **jira_client.py**: 
   - `search_issues('SPARK')` returns list including "SPARK-12345"
   - `get_issue('SPARK-12345')` fetches full details
   - `get_issue_comments('SPARK-12345')` fetches comments
4. **state_manager.py**: 
   - Checks if "SPARK-12345" in processed list (no)
   - Marks it as processed
5. **data_transformer.py**: 
   - `transform_issue()` converts raw JSON to clean format
   - Extracts text, formats dates, generates tasks
6. **data_transformer.py**: 
   - `write_jsonl()` appends to `jira_dataset.jsonl`
7. **state_manager.py**: 
   - `save_state()` updates `state/scrape_state.json`
8. **scraper.py**: Moves to next issue

---

## 🎯 Quick Reference: What Each File Does

| File | Purpose | When It Runs |
|------|---------|--------------|
| `main.py` | Entry point, CLI interface | First (you run this) |
| `src/scraper.py` | Orchestrates scraping process | Called by main.py |
| `src/jira_client.py` | Makes API calls to Jira | Called by scraper.py |
| `src/state_manager.py` | Tracks progress | Called by scraper.py |
| `src/data_transformer.py` | Converts data format | Called by scraper.py |

---

## 🚀 Running the Scraper - What Happens

### Command: `python main.py --projects SPARK --delay 1.5`

1. **main.py** executes
   - Parses `--projects SPARK` and `--delay 1.5`
   - Sets up logging

2. **JiraScraper** initializes
   - Creates JiraClient with 1.5s delay
   - Creates StateManager, loads existing state
   - Creates DataTransformer

3. **Scraping begins**
   - For each page of issues:
     - JiraClient fetches issues
     - StateManager checks which are new
     - DataTransformer converts each issue
     - StateManager saves progress

4. **Results**
   - `jira_dataset.jsonl` - Contains all scraped issues
   - `state/scrape_state.json` - Contains progress
   - Console shows progress and summary

---

## 💡 Key Concepts

### **Separation of Concerns**
- Each file has a single, clear responsibility
- Easy to test and maintain
- Can modify one layer without affecting others

### **Error Handling**
- JiraClient handles API errors
- StateManager handles file errors
- Each layer handles its own errors

### **Resumability**
- StateManager tracks progress
- Can stop and resume anytime
- No duplicate scraping

### **Batch Processing**
- Processes issues in batches
- Saves frequently (every N issues)
- Memory efficient

---

This architecture makes the code:
- ✅ **Maintainable** - Clear separation of concerns
- ✅ **Testable** - Each component can be tested independently
- ✅ **Resumable** - Can restart after interruptions
- ✅ **Scalable** - Can handle large datasets efficiently
- ✅ **Robust** - Comprehensive error handling

