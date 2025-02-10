def updateFeed(reader, rss_url):
    reader.add_feed(rss_url, exist_ok=True)  # Add feed if not already added
    reader.update_feeds()
    return reader.get_feed(rss_url)


def getEntries(reader, rss_url):
    entries = reader.get_entries(feed=rss_url, has_enclosures=False)
    entries = list(entries)
    return entries