from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers
import gzip
import io
import json
import requests

class GHArchiveStream(Stream):
    name = "github_events"
    path = "/2023-10-01-0.json.gz"
    primary_keys = ["id"]
    replication_key = None
    schema = th.PropertiesList(
        th.Property("type", th.StringType),
        th.Property("actor", th.ObjectType()),
        th.Property("repo", th.ObjectType()),
        th.Property("created_at", th.StringType),
        th.Property("org", th.ObjectType()),
        th.Property("payload", th.ObjectType()),
    ).to_dict()

    def get_records(self, context):
        """Get records from the source."""
        url = "https://data.gharchive.org" + self.path
        response = requests.get(url)
        gzdata = gzip.GzipFile(fileobj=io.BytesIO(response.content))
        # Process NDJSON format - each line is a separate JSON object
        for line in gzdata:
            if line.strip():  # Skip empty lines
                record = json.loads(line)
                yield record

    def parse_response(self, response):
        """Parse the response and return an iterator of result rows."""
        gzdata = gzip.GzipFile(fileobj=io.BytesIO(response.content)).read()
        data = json.loads(gzdata)
        for row in data:
            yield row

class TapGHArchive(Tap):
    name = "tap-gharchive"
    
    def discover_streams(self):
        """Return a list of discovered streams."""
        return [GHArchiveStream(self)] 