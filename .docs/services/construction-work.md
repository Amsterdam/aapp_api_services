# Construction Work

## Purpose of the service

The Construction Work service helps Amsterdam residents find information about construction and road works, follow projects that matter to them, and receive updates. It also gives authorized city staff and project publishers a way to manage project warnings.

## Main business rules
- Residents can browse active, publicly visible projects, search by project title or subtitle, and view project details such as location, work description, schedule, contacts, and related updates.
- Project lists can be ordered using a device's followed projects and its location. When a location is provided, nearby projects are prioritized; followed projects with recent content are prioritized above other followed projects.
- Residents can follow or unfollow projects on a device. A device can also remove all of its Construction Work data.
- Project news and road-work articles, along with project warnings, are presented as updates associated with projects. Recent updates are included with project details; update lists can be filtered by project and sorted.
- Only projects with usable descriptive sections are made active for public display. Hidden projects are excluded from public discovery.
- The service periodically imports project and article content from the city's DvO content source. Invalid individual source items should not prevent unrelated projects or articles from being processed. Projects no longer present in the source are deactivated, and inactive non-hidden projects not seen for five days are removed. Articles no longer present in the source are deactivated.
- Editors can manage publishers and assign them to projects. Publishers can access and manage warnings only for projects assigned to them; editors have broader management access.
- Authorized publishers and editors can create project warnings, update them, and attach images. A warning can trigger a push notification to devices following its project. New source articles can also trigger notifications to followers of their associated projects.

## Non-standard architectural decisions

- Construction Work combines two content paths: project and article details are synchronized from DvO, while warnings are created by authorized staff and publishers within the service.
- Project and article imagery, as well as warning imagery, uses the shared image service rather than storing image files as part of project content.
- Device identity and project follows are used to personalize discovery and target notifications; they do not represent resident accounts.
- The ETL does not fail for a single failing project/article. An error will be logged, but the pipeline continues with projects that can be loaded.

