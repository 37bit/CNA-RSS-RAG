from datetime import date, datetime
import requests
import os
import json

# Given an entry url, take the slug (last part of the url) - to be used as title
def get_slug(url):
    return "-".join(url.split("/")[-1].split("-")[:-1])


def update_downloaded_mt(metadata_file, entry_link, remove=False):

    # Create metadata_file if it does not exist
    if not os.path.exists(metadata_file):
        with open(metadata_file, "w") as f:
            json.dump({"downloaded_entries": {}}, f)

    # Get existing entries and update
    with open(metadata_file, "r") as f:
        meta = json.load(f)

        if "downloaded_entries" not in meta:
            meta["downloaded_entries"] = {}

        if not remove:
            meta["downloaded_entries"][entry_link] = date.today().strftime("%Y-%m-%d")
        else:
            if entry_link in meta["downloaded_entries"]:
                meta["downloaded_entries"].pop(entry_link)

    # Write back into json file
    with open(metadata_file, "w") as f:
        json.dump(meta, f)


# Read metadata file to obtain a list of entries that were downloaded today
def get_downloaded_mt(entries_dir, metadata_file=None):
    if not os.path.exists(metadata_file):
        print(f"Metadata file {metadata_file} does not exist.")
        metadata_entries = {}

    else:
        print(f"Metadata file {metadata_file} discovered.")
        with open(metadata_file, "r") as f:
            try:
                metadata_entries = json.load(f)["downloaded_entries"]
            except json.JSONDecodeError:
                print(f"{metadata_file} is corrupted. Please fix it or remove it.")
                exit(0)

        # List of existing entries in entries_dir
        existing_entries = list(
            filter(
                lambda e: os.path.isfile(entries_dir + "/" + e), os.listdir(entries_dir)
            )
        )

        # Remove existing files that are outdated
        # Also remove metadata entries if corresponding files do not exist
        for url, dwn_date in list(metadata_entries.items()):
            downloaded_date = datetime.strptime(dwn_date, "%Y-%m-%d").date()
            slug = get_slug(url)
            if downloaded_date < datetime.today().date() or not any(
                [
                    slug == os.path.splitext(existing_file)[0]
                    for existing_file in existing_entries
                ]
            ):
                update_downloaded_mt(metadata_file, url, remove=True)
                metadata_entries.pop(url)

        return metadata_entries


# Fetches the page of an entry, preprocesses the content and writes it to a txt file
def fetch_and_download(urls, entries_dir, metadata_file, parser, html_dir=None):
    if metadata_file is not None:
        metadata_entries = get_downloaded_mt(entries_dir, metadata_file)
        # print(list(metadata_entries.keys()))
        existing = [get_slug(url) for url in list(metadata_entries.keys())]
    else:
        existing = []

    downloaded = []
    for i, url in enumerate(urls):

        # Display download status
        print("{} - {}".format(i, url))

        # Retrieve url slug
        entry_name = get_slug(url)
        if len(entry_name) == 0:
            print("Incorrect slug. Skipping download.")
            continue

        part_path = os.path.join(entries_dir, entry_name + ".part")
        final_path = os.path.join(entries_dir, entry_name + ".txt")

        with requests.get(url) as response:

            try:
                # Download page for entry
                response.raise_for_status()  # Raises a HTTPError if there is one

                # Write entry to a file if it does not already exist (expected to be a txt file)
                if entry_name in existing:
                    print("Exists. Skipping download.")
                    continue

                with open(part_path, "w", encoding="utf-8") as file:

                    # Write html to an "archive" folder
                    if html_dir is not None:
                        os.makedirs(html_dir, exist_ok=True)
                        html_path = os.path.join(html_dir, entry_name + ".html")

                        # Remove html file first if it exists
                        if os.path.exists(html_path):
                            os.remove(html_path)
                        html = open(html_path, "w", encoding="utf-8")
                        html.write(response.text)
                        html.close()

                    # Extract main text from html and write into files
                    txt = parser(response.text)
                    file.write(txt)
                    update_downloaded_mt(metadata_file, url)
                    downloaded.append(entry_name + '.txt')

                # Create entries dir if it doesn't exist yet
                os.makedirs(entries_dir, exist_ok=True)

                # Remove entry with same name first if it exists
                if os.path.exists(final_path):
                    os.remove(final_path)
                os.rename(part_path, final_path)
            except BaseException:
                try:
                    os.remove(part_path)
                except Exception:
                    pass
                raise
            except requests.exceptions.RequestException:
                print("An error has occured. Skipping download.")
                continue

    return downloaded
