import openreview
from operator import itemgetter
from collections import defaultdict

from operator import itemgetter
import re
import pypandoc
import markdown
import getpass
import openreview
from operator import itemgetter
from collections import defaultdict
import re
import urllib.parse
from urllib.parse import urlparse, parse_qs


def parse_openreview_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    forum_id = query_params.get("id", [None])[0]

    referrer = query_params.get("referrer", [None])[0]
    if referrer:
        decoded_referrer = urllib.parse.unquote(referrer)
        venue_match = re.search(r"/group\?id=([^#]+)", decoded_referrer)
        venue_id = venue_match.group(1) if venue_match else None
    else:
        venue_id = None

    return forum_id, venue_id


# Ask for the URL
url = input("Enter the OpenReview URL: ")

# Parse the URL to get forum_id and venue_id
forum_id, venue_id = parse_openreview_url(url)

if not forum_id or not venue_id:
    print("Error: Couldn't extract forum ID or venue ID from the URL.")
    exit(1)

print(f"Extracted forum ID: {forum_id}")
print(f"Extracted venue ID: {venue_id}")

username = input("Enter your OpenReview username: ")
password = getpass.getpass("Enter your OpenReview password: ")

client = openreview.api.OpenReviewClient(
    baseurl="https://api2.openreview.net",
    username=username,
    password=password,
)

venue_group = client.get_group(venue_id)
notes = client.get_notes(forum=forum_id)


def extract_reviewer_id(signature):
    match = re.search(r"Reviewer_(\w+)$", signature[0])
    return match.group(1) if match else None


def generate_markdown(notes):
    # Separate the full paper and other notes
    full_paper = next((note for note in notes if note["replyto"] is None), None)
    other_notes = [note for note in notes if note["replyto"] is not None]

    markdown = ""

    # Process full paper
    if full_paper:
        markdown += "# Full Paper\n\n"
        markdown += process_full_paper(full_paper)

    # Create a dictionary to store notes by their ID
    notes_by_id = {note["id"]: note for note in other_notes}

    # Group top-level reviews by reviewer
    reviewer_groups = {}
    for note in other_notes:
        if note["replyto"] == full_paper["id"]:
            reviewer_id = extract_reviewer_id(note["signatures"])
            if reviewer_id:
                reviewer_groups[reviewer_id] = note["id"]

    # Process reviewer notes and their replies
    for reviewer_id, top_review_id in reviewer_groups.items():
        markdown += f"## {reviewer_id}\n\n"
        markdown += process_note_thread(top_review_id, notes_by_id)

    return markdown.strip()


def process_note_thread(note_id, notes_by_id, depth=0):
    markdown = ""
    note = notes_by_id[note_id]

    # Process the current note
    markdown += "  " * depth
    markdown += process_note(note, is_rebuttal="Authors" in note["signatures"][0])

    # Process replies to this note
    replies = [n for n in notes_by_id.values() if n["replyto"] == note_id]
    replies.sort(key=itemgetter("cdate"))

    for reply in replies:
        markdown += process_note_thread(reply["id"], notes_by_id, depth + 1)

    return markdown


def process_full_paper(paper):
    markdown = f"### Paper ID: {paper['id']}\n\n"

    content = paper["content"]
    markdown += f"**Title:** {content['title']['value']}\n\n"
    markdown += f"**Authors:** {', '.join(content['authors']['value'])}\n\n"
    markdown += f"**Abstract:** {content['abstract']['value']}\n\n"
    markdown += f"**Keywords:** {', '.join(content['keywords']['value'])}\n\n"
    markdown += f"**TLDR:** {content['TLDR']['value']}\n\n"

    markdown += "---\n\n"
    return markdown


def process_note(note, is_rebuttal=False):
    markdown = f"### {'Rebuttal to ' if is_rebuttal else ''}Note {note['number']} (ID: {note['id']})\n\n"

    content = note["content"]
    for key, value in content.items():
        if isinstance(value, dict) and "value" in value:
            markdown += f"**{key.capitalize()}:** {value['value']}\n\n"

    markdown += "---\n\n"
    return markdown


markdown_output = generate_markdown([note.__dict__ for note in notes])
print(markdown_output)
markdown_filename = f"{forum_id}.md"
with open(markdown_filename, "w", encoding="utf-8") as md_file:
    md_file.write(markdown_output)
print(f"Markdown file created: {markdown_filename}")


def markdown_to_odt(markdown_text, output_filename):
    # Convert markdown to HTML
    html = markdown.markdown(markdown_text)

    # Convert HTML to ODT
    pypandoc.convert_text(html, "odt", format="html", outputfile=output_filename)
    print(f"ODT file created: {output_filename}")


# Convert to ODT
markdown_to_odt(markdown_output, f"{forum_id}.odt")
