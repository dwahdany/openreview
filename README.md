# OpenReview Paper Fetcher

This script fetches paper details, reviews, and rebuttals from OpenReview and converts them to a formatted ODT document.

## Features

- Extracts forum ID and venue ID from an OpenReview URL
- Fetches paper details, reviews, and rebuttals
- Generates a formatted markdown document
- Converts the markdown to an ODT file

## Requirements

- Python 3.6+
- Required packages: openreview, pypandoc, markdown

A conda environment file (`env.yml`) is provided for easy setup.

## Setup

1. Create the conda environment:
```
conda env create -f env.yml
```

2. Activate the environment:
```
conda activate openreview-fetcher
```

## Usage

1. Run the script: `python get_reviews.py`
2. Enter the full OpenReview URL when prompted (like `https://openreview.net/forum?id=XXXXXXXXXXXX&referrer=%5BAuthor%20Console%5D(%2Fgroup%3Fid%3DConference.org%2FYYYY%2FMeeting%2FAuthors%23your-submissions)`)
3. Provide your OpenReview username and password
4. The script will generate an `output_document.odt` file in the same directory

## Note

Ensure you have the necessary permissions to access the paper on OpenReview.