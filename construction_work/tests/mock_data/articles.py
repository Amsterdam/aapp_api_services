import datetime

MOCK_DATA = [
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
        "type": "work",
        "url": "https://www.amsterdam.nl/fizzbuzz-article",
        "creation_date": "2023-01-01T00:00:00+00:00",
        "modification_date": "2023-01-20T00:00:00+00:00",
        "publication_date": "2023-01-01T00:00:00+00:00",
        "expiration_date": "2023-02-01T00:00:00+00:00",
    },
]
