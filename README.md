# Apache Jira Scraper

A robust, fault-tolerant web scraping system that extracts public issue data from Apache's Jira instance and transforms it into a structured JSONL format suitable for training Large Language Models (LLMs).

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Setup](#setup)
- [Usage](#usage)
- [Edge Cases Handled](#edge-cases-handled)
- [Optimization Decisions](#optimization-decisions)
- [Future Improvements](#future-improvements)

## Overview

This project implements a complete data scraping and transformation pipeline that:

- Scrapes issue data from Apache's public Jira projects using the REST API
- Handles network failures, rate limiting, and data inconsistencies gracefully
- Supports resumable scraping with state persistence
- Transforms raw Jira data into clean JSONL format with derived tasks for LLM training

### Why REST API Instead of HTML Scraping?

While the assignment mentioned exploring solutions outside HTML scraping, we chose to use the Jira REST API because:

1. **Reliability**: API responses are structured and consistent, eliminating parsing errors
2. **Efficiency**: Direct data access without HTML parsing overhead
3. **Rate Limits**: APIs typically have better-documented rate limits
4. **Completeness**: APIs provide all data fields without needing to render pages
5. **Maintainability**: Less brittle than HTML scraping when Jira updates their UI

## Features

### Core Functionality

- ✅ **Multi-Project Scraping**: Scrape multiple Jira projects in a single run
- ✅ **Comprehensive Data Extraction**: Issues, comments, metadata (status, priority, assignee, labels, timestamps)
- ✅ **Resumable Scraping**: Automatic state management allows resuming from interruptions
- ✅ **Robust Error Handling**: Handles HTTP 429, 5xx errors, timeouts, and connection failures
- ✅ **Rate Limiting**: Built-in delays and exponential backoff to respect API limits
- ✅ **JSONL Output**: Clean, structured format suitable for LLM training
- ✅ **Derived Tasks**: Automatically generates summarization, classification, and Q&A tasks

### Fault Tolerance

- Automatic retry with exponential backoff
- State persistence for crash recovery
- Graceful handling of malformed data
- Progress tracking with detailed logging

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                      main.py                            │
│              (CLI Interface & Orchestration)            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   scraper.py                            │
│         (High-level Scraping Orchestration)             │
└──────────┬──────────────┬──────────────┬───────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────────┐
    │  Jira    │   │  State   │   │    Data      │
    │  Client  │   │ Manager  │   │ Transformer  │
    └──────────┘   └──────────┘   └──────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────────┐
    │  REST    │   │   JSON   │   │   JSONL      │
    │   API    │   │   State  │   │   Output     │
    └──────────┘   └──────────┘   └──────────────┘
```

### Component Descriptions

#### 1. `jira_client.py` - API Client
- Handles all HTTP communication with Jira REST API
- Implements retry logic with exponential backoff
- Manages rate limiting (HTTP 429) and server errors (5xx)
- Handles timeouts and connection errors gracefully

#### 2. `state_manager.py` - State Management
- Tracks processed issues per project
- Stores pagination progress
- Enables seamless resumption after interruptions
- JSON-based persistence

#### 3. `data_transformer.py` - Data Transformation
- Converts raw Jira API responses to structured JSONL format
- Extracts plain text from HTML/structured fields
- Generates derived tasks (summarization, classification, Q&A)
- Handles missing or malformed data gracefully

#### 4. `scraper.py` - Main Scraper
- Orchestrates the scraping process
- Manages pagination across projects
- Coordinates state management and data transformation
- Provides progress tracking

#### 5. `main.py` - CLI Interface
- Command-line interface for running the scraper
- Configurable parameters (projects, output file, delays, etc.)
- Provides statistics and summaries

### Data Flow

1. **Initialization**: Load state, verify projects exist
2. **Pagination Loop**: 
   - Fetch page of issues from Jira API
   - For each issue: fetch detailed data and comments
   - Transform to JSONL format
   - Update state
3. **Batch Writing**: Periodically write batches to JSONL file
4. **State Persistence**: Save progress after each batch
5. **Completion**: Generate summary statistics

## Setup

### Prerequisites

- Python 3.7 or higher
- Internet connection (to access Apache Jira)

### Installation

1. **Clone or download the repository**:
   ```bash
   cd WEB_SCRAPER
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Environment Configuration

No API keys or authentication required - uses Apache's public Jira instance.

## Usage

### Basic Usage

Scrape default projects (SPARK, HADOOP, FLINK):

```bash
python main.py
```

### Advanced Usage

Scrape specific projects:

```bash
python main.py --projects SPARK HADOOP FLINK KAFKA
```

Customize output file:

```bash
python main.py --output my_dataset.jsonl
```

Adjust rate limiting:

```bash
python main.py --delay 2.0  # 2 seconds between requests
```

Change batch size:

```bash
python main.py --batch-size 20  # Save every 20 issues
```

### Resume Interrupted Scrapes

If scraping is interrupted (Ctrl+C or crash), simply run the same command again. The scraper will automatically resume from where it left off:

```bash
python main.py --projects SPARK HADOOP FLINK
```

### Reset State

To start fresh (re-scrape everything):

```bash
python main.py --reset
```

Reset a specific project:

```bash
python main.py --reset-project SPARK
```

### Command-Line Options

```
usage: main.py [-h] [--projects PROJECTS [PROJECTS ...]] 
               [--output OUTPUT] [--state-dir STATE_DIR]
               [--max-results MAX_RESULTS] [--batch-size BATCH_SIZE]
               [--delay DELAY] [--reset] [--reset-project RESET_PROJECT]

optional arguments:
  -h, --help            Show help message
  --projects            Jira project keys (default: SPARK HADOOP FLINK)
  --output              Output JSONL file path (default: jira_dataset.jsonl)
  --state-dir           Directory for state files (default: state)
  --max-results         Results per page (default: 50)
  --batch-size          Batch size for saving (default: 10)
  --delay               Delay between requests in seconds (default: 1.0)
  --reset               Reset state and start fresh
  --reset-project       Reset state for a specific project
```

### Output Format

The scraper generates a JSONL file where each line is a JSON object representing one issue:

```json
{
  "issue_key": "SPARK-12345",
  "project": "Apache Spark",
  "title": "Issue title",
  "description": "Issue description as plain text",
  "status": "Resolved",
  "issue_type": "Bug",
  "priority": "High",
  "reporter": "John Doe",
  "assignee": "Jane Smith",
  "created": "2024-01-15 10:30:00 UTC",
  "updated": "2024-01-20 14:20:00 UTC",
  "resolved": "2024-01-20 14:20:00 UTC",
  "labels": ["bug", "spark-core"],
  "components": ["SQL", "Core"],
  "comments": [
    {
      "author": "Jane Smith",
      "body": "Comment text",
      "created": "2024-01-16 09:00:00 UTC",
      "updated": "2024-01-16 09:00:00 UTC"
    }
  ],
  "comment_count": 1,
  "metadata": {
    "raw_issue_key": "SPARK-12345",
    "scraped_at": "2024-01-25T12:00:00.000000",
    "source": "apache-jira"
  },
  "derived_tasks": {
    "summarization": {
      "instruction": "Summarize the following Jira issue:",
      "input": "...",
      "output": "..."
    },
    "classification": {
      "instruction": "Classify the following Jira issue by type and status:",
      "input": "...",
      "output": "..."
    },
    "qa_generation": {
      "question": "What is the issue SPARK-12345 about?",
      "context": "...",
      "answer": "..."
    }
  }
}
```

## Edge Cases Handled

### 1. Network Failures

**Problem**: Network interruptions, connection timeouts, DNS failures

**Solution**:
- Retry logic with exponential backoff (up to 5 retries)
- Configurable timeout values
- Graceful degradation with detailed error logging

**Implementation**: `jira_client.py` catches `requests.exceptions.Timeout` and `requests.exceptions.ConnectionError`

### 2. HTTP 429 (Rate Limiting)

**Problem**: Jira API rate limiting when making too many requests

**Solution**:
- Detects HTTP 429 responses
- Reads `Retry-After` header for wait time
- Automatically waits and retries
- Configurable delay between requests (`--delay` flag)

**Implementation**: `jira_client.py` checks status code 429 and implements retry-after logic

### 3. HTTP 5xx (Server Errors)

**Problem**: Jira server experiencing issues (500, 502, 503, 504)

**Solution**:
- Exponential backoff retry strategy
- Maximum retry limit to prevent infinite loops
- Logs errors for monitoring
- Continues with next issue if retries exhausted

**Implementation**: `jira_client.py` handles 5xx errors with exponential backoff

### 4. Empty or Malformed Data

**Problem**: API returns empty responses, null fields, or invalid JSON

**Solution**:
- Validates JSON parsing with try-except
- Checks for None/empty responses
- Skips invalid issues with logging
- Handles missing fields gracefully in transformer

**Implementation**: 
- `jira_client.py`: Validates JSON parsing
- `data_transformer.py`: Handles None/empty fields with defaults

### 5. Interrupted Scrapes

**Problem**: Process crashes, user interruption (Ctrl+C), power loss

**Solution**:
- State persistence after each batch
- Tracks processed issue keys per project
- Stores pagination position
- Automatic resumption on restart

**Implementation**: `state_manager.py` maintains persistent state, `scraper.py` checks processed issues before processing

### 6. Missing or Partial Data

**Problem**: Issues missing comments, fields, or incomplete metadata

**Solution**:
- Optional field handling with defaults
- Separate API call for comments if missing
- Graceful degradation (logs warning, continues)
- Uses empty strings/arrays for missing data

**Implementation**: `data_transformer.py` uses `.get()` with defaults, checks for field existence

### 7. HTML Content in Fields

**Problem**: Description and comments contain HTML markup

**Solution**:
- Extracts plain text from HTML using regex
- Handles both rendered and raw fields
- Preserves whitespace structure
- Falls back to raw text if parsing fails

**Implementation**: `data_transformer.py` `extract_text_content()` method

### 8. Pagination Edge Cases

**Problem**: Total count changes during scraping, empty pages, inconsistent page sizes

**Solution**:
- Dynamically checks remaining issues
- Handles empty result pages gracefully
- Continues until no more issues returned
- Updates progress incrementally

**Implementation**: `scraper.py` checks `len(issues) < max_results_per_page` to detect end

### 9. Concurrent Failures

**Problem**: Multiple consecutive API failures

**Solution**:
- Tracks consecutive failure count
- Stops after threshold (5 consecutive failures)
- Prevents infinite retry loops
- Logs detailed error information

**Implementation**: `scraper.py` maintains `consecutive_failures` counter

### 10. Large Datasets

**Problem**: Projects with thousands of issues, memory constraints

**Solution**:
- Batched writing (configurable batch size)
- Streams data to file instead of keeping in memory
- Processes one page at a time
- Incremental state updates

**Implementation**: `scraper.py` writes in batches, `data_transformer.py` appends to file

## Optimization Decisions

### 1. REST API Over HTML Scraping

**Decision**: Use Jira REST API instead of HTML scraping

**Rationale**:
- Faster (direct data access)
- More reliable (structured JSON)
- Less brittle (API contracts vs. DOM structure)
- Complete data access (all fields available)

**Trade-off**: Requires API endpoint knowledge, but publicly documented

### 2. Incremental State Persistence

**Decision**: Save state after each batch (default: 10 issues)

**Rationale**:
- Minimizes data loss on crash
- Allows frequent checkpoints
- Small overhead (writes small JSON file)

**Trade-off**: More disk I/O, but acceptable for reliability

### 3. Batch Writing

**Decision**: Write to JSONL in batches instead of one-by-one

**Rationale**:
- Reduces file I/O operations
- Improves performance for large datasets
- Still frequent enough for recovery

**Trade-off**: Slightly less frequent saves, but better performance

### 4. Separate Comment Fetching

**Decision**: Fetch comments separately from issue details

**Rationale**:
- Some issues have many comments (could slow main query)
- Allows parallelization opportunity (future improvement)
- Handles cases where comments are missing from search results

**Trade-off**: Extra API call per issue, but ensures completeness

### 5. Rate Limiting Delays

**Decision**: Configurable delay between requests (default: 1 second)

**Rationale**:
- Prevents hitting rate limits
- Respectful to Apache's infrastructure
- Configurable for different scenarios

**Trade-off**: Slower scraping, but prevents bans and errors

### 6. Exponential Backoff

**Decision**: Exponential backoff for retries (2^attempt seconds)

**Rationale**:
- Reduces load on failing server
- Increases chance of recovery after temporary issues
- Industry-standard approach

**Trade-off**: Slower recovery, but prevents server overload

### 7. Skip Processed Issues

**Decision**: Track processed issue keys and skip duplicates

**Rationale**:
- Enables safe resumption
- Prevents duplicate data
- Efficient (set-based lookup)

**Trade-off**: Requires state storage, but minimal overhead

### 8. JSONL Format

**Decision**: Output in JSONL (JSON Lines) format

**Rationale**:
- Standard format for LLM training
- Streamable (one object per line)
- Easy to parse incrementally
- Works with common ML tools

**Trade-off**: Less human-readable than pretty JSON, but better for processing

### 9. Derived Tasks Generation

**Decision**: Generate summarization, classification, and Q&A tasks

**Rationale**:
- Ready-to-use for LLM training
- Adds value beyond raw data
- Demonstrates understanding of LLM training needs

**Trade-off**: Increases output size, but enhances utility

### 10. Progress Tracking

**Decision**: Use tqdm for progress bars and detailed logging

**Rationale**:
- User feedback during long runs
- Helps identify stuck processes
- Professional user experience

**Trade-off**: Slight performance overhead, but improves usability

## Future Improvements

### 1. Parallel Processing

**Opportunity**: Fetch multiple issues/comments in parallel

**Implementation**: Use `concurrent.futures.ThreadPoolExecutor` or `asyncio`

**Benefit**: Significantly faster scraping for large datasets

**Consideration**: Need careful rate limiting management

### 2. Incremental Updates

**Opportunity**: Only fetch new/updated issues since last scrape

**Implementation**: Use JQL queries with date filters, store last update timestamp

**Benefit**: Much faster for regular updates

### 3. Data Validation

**Opportunity**: Validate JSONL output against schema

**Implementation**: Use JSON Schema or Pydantic models

**Benefit**: Ensures data quality, catches bugs early

### 4. Statistics and Reporting

**Opportunity**: Generate detailed statistics about scraped data

**Implementation**: Analyze JSONL file, generate reports

**Benefit**: Quality metrics, data insights

### 5. Configurable Derived Tasks

**Opportunity**: Allow custom task generation templates

**Implementation**: Template-based task generation with configuration file

**Benefit**: Flexibility for different LLM training scenarios

### 6. Caching

**Opportunity**: Cache API responses for development/debugging

**Implementation**: Use `requests-cache` or local file cache

**Benefit**: Faster iteration, offline development

### 7. Better HTML Parsing

**Opportunity**: Use proper HTML parser (BeautifulSoup) instead of regex

**Implementation**: Add BeautifulSoup dependency

**Benefit**: More robust HTML extraction, handles edge cases

### 8. Streaming Output

**Opportunity**: Stream directly to cloud storage (S3, GCS)

**Implementation**: Add cloud storage adapters

**Benefit**: No local disk space needed, direct integration

### 9. Monitoring and Alerting

**Opportunity**: Add metrics collection and alerting

**Implementation**: Integrate with Prometheus, Grafana, or similar

**Benefit**: Production-ready monitoring

### 10. Multi-Format Output

**Opportunity**: Support multiple output formats (CSV, Parquet, etc.)

**Implementation**: Add format converters

**Benefit**: Flexibility for different downstream tools

## Troubleshooting

### Issue: Rate limiting errors

**Solution**: Increase `--delay` value (e.g., `--delay 2.0`)

### Issue: Out of memory

**Solution**: Reduce `--batch-size` (e.g., `--batch-size 5`)

### Issue: Stuck on same issue

**Solution**: Check logs, may need to reset project: `--reset-project PROJECT_KEY`

### Issue: Connection errors

**Solution**: Check internet connection, increase timeout in `jira_client.py`

### Issue: Empty output file

**Solution**: Check logs for errors, verify project keys are correct

## License

This project is for educational/assignment purposes. Please respect Apache's Terms of Service and rate limits when using their public Jira instance.

## Contact

For questions or issues, please refer to the assignment guidelines or contact the assignment reviewers.

---

**Note**: This scraper uses only publicly available data from Apache Jira and respects rate limits to avoid overloading their infrastructure.

