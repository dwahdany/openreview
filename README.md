# OpenReview Review Fetcher

This script fetches paper details, reviews, and rebuttals from OpenReview and converts them to formatted ODT and Markdown documents.

## Features

- Extracts forum ID and venue ID from an OpenReview URL
- Optional credential caching
- Fetches paper details, reviews, and rebuttals
- Generates a formatted markdown document
- Converts the markdown to an ODT file

## Requirements

- Python (tested with 3.11)
- Dependencies, see conda environment file (`env.yml`)

## Setup

### Option 1: Using conda
1. Create the conda environment:
```
conda env create -f env.yml
```

2. Activate the environment:
```
conda activate openreview
```

### Option 2: Using uv (faster)
1. Install uv if you haven't already:

2. Run it with uv `uv run get_reviews.py`

## Usage

1. Run the script: `python get_reviews.py`
2. Enter the full OpenReview URL when prompted (like `https://openreview.net/forum?id=XXXXXXXXXXXX&referrer=%5BAuthor%20Console%5D(%2Fgroup%3Fid%3DConference.org%2FYYYY%2FMeeting%2FAuthors%23your-submissions)`)
3. Provide your OpenReview username and password
4. The script will generate an `$FORUM_ID.odt` and `$FORUM_ID.md` file in the same directory, where `$FORUM_ID` is the ID of the forum extracted from step 2.

## Note

Ensure you have the necessary permissions to access the paper on OpenReview.