""" Transform data into suitable format for ingestion """

from datetime import datetime

from django.conf import settings


def projects(data):
    """Transform project data"""
    for project in data:
        if project.get("image") is not None:
            project["image"] = _image(project["image"])
        if project.get("images") is not None:
            project["images"] = _images(project["images"])

        date_string = project.get("modified", settings.EPOCH)
        project["modified"] = datetime.strptime(date_string, settings.DATE_FORMAT_IPROX)
    return data


def articles(data):
    """Transform article data"""
    for article in data:
        if article.get("image") is not None:
            article["image"] = _image(article["image"])

        date_string = article.get("modified", settings.EPOCH)
        article["modified"] = datetime.strptime(date_string, settings.DATE_FORMAT_IPROX)
    return data


def _images(images_set):
    """get images"""
    for idx, _ in enumerate(images_set):
        images_set[idx] = _image(images_set[idx])
    return images_set

def _image(image_set):
    """Rename url to uri"""
    for idx, _ in enumerate(image_set.get("sources", [])):
        image_set["sources"][idx]["uri"] = image_set["sources"][idx].pop("url")

    return image_set
