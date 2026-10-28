# Construction Work

Construction Work publishes project information, related articles, and warnings.
Existing projects retain their identity and relationships while content moves
from Iprox to Drupal.

## Images

Project and article images contain one or more size variants associated with an
image set. Each variant contains its URL and dimensions. A URL may occur only
once per project or article.

Public image responses keep their existing structure. The public image ID and
image-set ID both identify the image set, rather than a legacy Iprox image or a
local variant. Aspect ratio is calculated from the first variant's dimensions;
it is unavailable when that variant's height is zero. Alternative text is
currently unavailable and is returned as null.

## Migration and rollout

Take and verify a restorable database backup before migrating. Pause ingestion
and coordinate the application deployment with the database migration; the old
and new image structures are not compatible.

Existing image URLs, dimensions, image-set associations, and project/article
relationships are retained. Legacy image identifiers, stored aspect ratios, and
alternative text are intentionally discarded. Image containers without variants
do not produce an image in the new structure. The image migration is
irreversible: rollback requires restoring the backup.

Duplicate URLs within the same project or article, empty URLs, URLs exceeding
2048 characters, and non-positive image-set IDs must be resolved before
migration. Such records stop migration rather than being silently discarded.
Check image-set associations against the image service beforehand: some legacy
records may still contain the historical placeholder ID of 1, which cannot be
distinguished automatically from a genuine ID.

Drupal IDs are the canonical identifiers for imported projects and articles
and are used by their public representations. Legacy Iprox IDs are optional
and are retained only on records that already have them; new Drupal content
does not receive an invented Iprox ID. Drupal IDs must be unique when supplied.

Existing projects receive a Drupal ID only when the authoritative mapping
contains a match. Unmatched legacy records are not assigned guessed IDs; a
subsequent normal synchronization treats records without a Drupal ID as unseen.
The first synchronization should not send notifications for all imported
articles. Because it also skips cleanup, unmatched legacy records can remain
visible until a later normal synchronization.
