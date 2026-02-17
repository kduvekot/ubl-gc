#!/usr/bin/env python3
"""
Explore a public Google Drive folder without authentication.
Uses the embeddedfolderview endpoint which works for public folders.
"""
import re
import sys
import json
import urllib.request
from html.parser import HTMLParser
from datetime import datetime


class DriveEmbedParser(HTMLParser):
    """Parse the embedded folder view HTML to extract file/folder entries."""

    def __init__(self):
        super().__init__()
        self.entries = []
        self.current_entry = None
        self.in_title = False
        self.in_modified = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # New entry div
        if tag == 'div' and attrs_dict.get('class') == 'flip-entry':
            self.current_entry = {
                'id': attrs_dict.get('id', '').replace('entry-', ''),
                'type': None,
                'name': None,
                'url': None,
                'modified': None
            }

        # Link with folder/file URL
        if tag == 'a' and self.current_entry and 'href' in attrs_dict:
            url = attrs_dict['href']
            self.current_entry['url'] = url
            if '/folders/' in url:
                self.current_entry['type'] = 'folder'
                # Extract folder ID from URL
                match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
                if match:
                    self.current_entry['id'] = match.group(1)
            elif '/file/' in url:
                self.current_entry['type'] = 'file'
                match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
                if match:
                    self.current_entry['id'] = match.group(1)

        # Title div
        if tag == 'div' and attrs_dict.get('class') == 'flip-entry-title':
            self.in_title = True

        # Modified time div
        if tag == 'div' and attrs_dict.get('class') == 'flip-entry-last-modified':
            self.in_modified = True

    def handle_data(self, data):
        if self.current_entry:
            if self.in_title:
                self.current_entry['name'] = data.strip()
                self.in_title = False
            elif self.in_modified and data.strip():
                self.current_entry['modified'] = data.strip()

    def handle_endtag(self, tag):
        if tag == 'div' and self.current_entry and self.current_entry.get('name'):
            self.entries.append(self.current_entry)
            self.current_entry = None
        if tag == 'div':
            self.in_modified = False


def fetch_folder_contents(folder_id):
    """Fetch and parse a public Google Drive folder."""
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            html = response.read().decode('utf-8')

        # Extract folder title
        title_match = re.search(r'<title>([^<]+)</title>', html)
        folder_name = title_match.group(1) if title_match else "Unknown"

        # Parse entries
        parser = DriveEmbedParser()
        parser.feed(html)

        return folder_name, parser.entries

    except Exception as e:
        print(f"Error fetching {folder_id}: {e}", file=sys.stderr)
        return None, []


def explore_folder_recursive(folder_id, folder_name, path="/", depth=0, max_depth=10):
    """Recursively explore a folder and all subfolders."""
    indent = "  " * depth

    if depth > max_depth:
        print(f"{indent}[max depth reached]", file=sys.stderr)
        return None

    print(f"{indent}📁 {folder_name}")

    name, entries = fetch_folder_contents(folder_id)

    result = {
        'id': folder_id,
        'name': folder_name,
        'path': path,
        'type': 'folder',
        'children': []
    }

    # Separate folders and files
    folders = [e for e in entries if e['type'] == 'folder']
    files = [e for e in entries if e['type'] == 'file']

    # Show files first
    for entry in files:
        print(f"{indent}  📄 {entry['name']} (modified: {entry['modified']})")
        result['children'].append({
            'id': entry['id'],
            'name': entry['name'],
            'path': f"{path}{entry['name']}",
            'type': 'file',
            'modified': entry['modified'],
            'url': entry['url']
        })

    # Then recurse into folders
    for entry in folders:
        subfolder = explore_folder_recursive(
            entry['id'],
            entry['name'],
            path=f"{path}{entry['name']}/",
            depth=depth + 1,
            max_depth=max_depth
        )
        if subfolder:
            result['children'].append(subfolder)

    return result


def count_items(tree):
    """Count files and folders recursively."""
    files = 0
    folders = 0

    for child in tree.get('children', []):
        if child['type'] == 'folder':
            folders += 1
            f, d = count_items(child)
            files += f
            folders += d
        else:
            files += 1

    return files, folders


def main():
    if len(sys.argv) < 2:
        print("Usage: explore-public-drive.py <folder_id> [output.json]")
        print("\nExample:")
        print("  explore-public-drive.py 1SVXV_8CF4ib9YsVZ6G7AqIP3gNK6q3Gj output.json")
        sys.exit(1)

    folder_id = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print("=" * 70)
    print("Exploring Public Google Drive Folder")
    print("=" * 70)
    print(f"Folder ID: {folder_id}")
    print(f"URL: https://drive.google.com/drive/folders/{folder_id}")
    print()

    tree = explore_folder_recursive(folder_id, "Root", path="/")

    if tree:
        files, folders = count_items(tree)

        print()
        print("=" * 70)
        print(f"Summary: {files} files, {folders} folders")
        print("=" * 70)

        if output_file:
            output = {
                '_metadata': {
                    'folder_id': folder_id,
                    'url': f"https://drive.google.com/drive/folders/{folder_id}",
                    'explored_at': datetime.utcnow().isoformat() + 'Z',
                    'total_files': files,
                    'total_folders': folders
                },
                'tree': tree
            }

            with open(output_file, 'w') as f:
                json.dump(output, f, indent=2)

            print(f"\nOutput saved to: {output_file}")


if __name__ == "__main__":
    main()
