import datetime

projects = [
    {
        "foreign_id": 2048,
        "active": True,
        "title": "title first project",
        "subtitle": "subtitle first project",
        "coordinates": {"lat": 1.0, "lon": 1.0},
        "sections": {},
        "contacts": {},
        "timeline": {},
        "image": {},
        "images": [],
        "url": "https://www.amsterdam.nl/foobar",
        "creation_date": "2023-01-01T00:00:00+00:00",
        "modification_date": "2023-01-20T00:00:00+00:00",
        "publication_date": "2023-01-01T00:00:00+00:00",
        "expiration_date": "2023-02-01T00:00:00+00:00",
    },
    {
        "foreign_id": 4096,
        "active": True,
        "title": "title second project",
        "subtitle": "subtitle second project",
        "coordinates": None,
        "sections": {},
        "contacts": {},
        "timeline": {},
        "image": {},
        "images": [],
        "url": "https://www.amsterdam.nl/fizzbuzz",
        "creation_date": "2023-01-01T00:00:00+00:00",
        "modification_date": "2023-01-20T00:00:00+00:00",
        "publication_date": "2023-01-01T00:00:00+00:00",
        "expiration_date": "2023-02-01T00:00:00+00:00",
    },
]

articles = [
    {
        "foreign_id": 128,
        "active": True,
        "last_seen": datetime.datetime.strptime(
            "2023-01-01T00:00:00", "%Y-%d-%mT%H:%M:%S"
        ),
        "title": "title of first article",
        "intro": "intro for first article",
        "body": {
            "content": {"html": "html content", "text": "text content"},
            "preface": {"html": "html content", "text": "text content"},
            "summary": {"html": "html content", "text": "text content"},
        },
        "image": {},
        "type": "work",
        "url": "https://www.amsterdam.nl/foobar-article",
        "creation_date": "2023-01-01T00:00:00+00:00",
        "modification_date": "2023-01-20T00:00:00+00:00",
        "publication_date": "2023-01-01T00:00:00+00:00",
        "expiration_date": "2023-02-01T00:00:00+00:00",
    },
    {
        "foreign_id": 256,
        "active": True,
        "last_seen": datetime.datetime.strptime(
            "2023-01-01T12:00:00", "%Y-%d-%mT%H:%M:%S"
        ),
        "title": "title of second article",
        "intro": "intro for second article",
        "body": {
            "content": {"html": "html content", "text": "text content"},
            "preface": {"html": "html content", "text": "text content"},
            "summary": {"html": "html content", "text": "text content"},
        },
        "image": {},
        "type": "work",
        "url": "https://www.amsterdam.nl/fizzbuzz-article",
        "creation_date": "2023-01-01T00:00:00+00:00",
        "modification_date": "2023-01-20T00:00:00+00:00",
        "publication_date": "2023-01-01T00:00:00+00:00",
        "expiration_date": "2023-02-01T00:00:00+00:00",
    },
]

devices = [
    {
        "device_id": "foobar_device1",
        "firebase_token": "foobar_token1",
        "os": "ios",
    },
    {
        "device_id": "foobar_device2",
        "firebase_token": "foobar_token2",
        "os": "android",
    },
]

warning_message = {
    "title": "warning message title",
    "body": "warning message body",
    "publication_date": "2023-10-10",
    "modification_date": "2023-10-11",
}
