# Quick Start Guide

Get up and running with the Apache Jira Scraper in 5 minutes!

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Verify Setup

```bash
python setup.py
```

This will check that everything is installed correctly.

## 3. Test API Connection (Optional)

```bash
python test_api_connection.py
```

This verifies you can connect to Apache Jira.

## 4. Run the Scraper

### Basic Usage

Scrape the default projects (SPARK, HADOOP, FLINK):

```bash
python main.py
```

### Custom Projects

Scrape specific projects:

```bash
python main.py --projects SPARK KAFKA CASSANDRA
```

### Custom Output

Save to a different file:

```bash
python main.py --output my_data.jsonl
```

## 5. Resume After Interruption

If scraping is interrupted (Ctrl+C), just run the same command again:

```bash
python main.py
```

The scraper will automatically resume from where it left off!

## Common Options

```bash
# Slower scraping (more respectful of rate limits)
python main.py --delay 2.0

# Save more frequently
python main.py --batch-size 5

# Start fresh (re-scrape everything)
python main.py --reset
```

## Output

The scraper creates a `jira_dataset.jsonl` file (or your custom filename) with one JSON object per line. Each line represents one Jira issue with all its data and derived tasks for LLM training.

## Troubleshooting

- **Rate limiting errors?** Increase delay: `--delay 2.0`
- **Out of memory?** Reduce batch size: `--batch-size 5`
- **Want to start over?** Use `--reset` flag

For detailed information, see [README.md](README.md).

