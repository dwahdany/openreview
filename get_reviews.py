import base64
import getpass
import json
import os
import re
import urllib.parse
from operator import itemgetter
from urllib.parse import parse_qs, urlparse

import markdown
import openreview
import pypandoc
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_key():
    # Use a fixed salt (not ideal, but better than nothing)
    salt = b"fixed_salt_for_openreview"
    # Use the machine's hostname as a basis for the key
    hostname = os.uname().nodename.encode()
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(hostname))
    return key


def encrypt(text):
    f = Fernet(get_key())
    return f.encrypt(text.encode()).decode()


def decrypt(text):
    f = Fernet(get_key())
    return f.decrypt(text.encode()).decode()


def load_cached_credentials():
    if os.path.exists("credentials.enc"):
        with open("credentials.enc", "r") as f:
            creds = json.loads(decrypt(f.read()))
        return creds["username"], creds["password"]
    return None, None


def save_credentials(username, password):
    creds = {"username": username, "password": password}
    encrypted = encrypt(json.dumps(creds))
    with open("credentials.enc", "w") as f:
        f.write(encrypted)


def get_credentials():
    username, password = load_cached_credentials()
    if username and password:
        print("Using cached credentials.")
        return username, password

    username = input("Enter your OpenReview username: ")
    password = getpass.getpass("Enter your OpenReview password: ")

    cache_choice = input(
        "Do you want to cache these credentials? Note that this is insecure. (y/N): "
    ).lower()
    if cache_choice == "y":
        save_credentials(username, password)
        print("Credentials cached.")

    return username, password


def get_unique_filename(base_filename):
    counter = 1
    filename, extension = os.path.splitext(base_filename)
    while os.path.exists(base_filename):
        base_filename = f"{filename}_{counter}{extension}"
        counter += 1
    return base_filename


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


def markdown_to_odt(markdown_text, output_filename):
    # Convert markdown to HTML
    html = markdown.markdown(markdown_text)

    # Convert HTML to ODT
    pypandoc.convert_text(html, "odt", format="html", outputfile=output_filename)
    print(f"ODT file created: {output_filename}")


if __name__ == "__main__":
    # Ask for the URL
    url = input("Enter the OpenReview URL: ")

    # Parse the URL to get forum_id and venue_id
    forum_id, venue_id = parse_openreview_url(url)

    if not forum_id or not venue_id:
        print("Error: Couldn't extract forum ID or venue ID from the URL.")
        exit(1)

    print(f"Extracted forum ID: {forum_id}")
    print(f"Extracted venue ID: {venue_id}")

    username, password = get_credentials()

    client = openreview.api.OpenReviewClient(
        baseurl="https://api2.openreview.net",
        username=username,
        password=password,
    )

    venue_group = client.get_group(venue_id)
    notes = client.get_notes(forum=forum_id)
    markdown_output = generate_markdown([note.__dict__ for note in notes])
    print(markdown_output)
    markdown_filename = f"{forum_id}.md"
    markdown_filename = get_unique_filename(markdown_filename)
    with open(markdown_filename, "w", encoding="utf-8") as md_file:
        md_file.write(markdown_output)
    print(f"Markdown file created: {markdown_filename}")

    # Convert to ODT
    odt_filename = f"{forum_id}.odt"
    odt_filename = get_unique_filename(odt_filename)
    markdown_to_odt(markdown_output, odt_filename)
