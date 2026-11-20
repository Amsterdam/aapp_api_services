# Image Service

The image service stores uploaded or URL-sourced images as three size variants
for use by other backend services.

## Business Rules

- A URL-derived identifier is an upsert key: repeated requests return the same
  image set, including when another upload has already used that identifier.
- Direct uploads with an existing explicit identifier are rejected. Uploads
  without an identifier may create separate image sets.
- Invalid URL input is rejected before downloading or storing an image.

## Consistency

URL creation is coordinated with a PostgreSQL transaction-scoped advisory lock.
The database uniqueness constraint also protects against competing direct
uploads, which do not take that lock.

Database transactions cannot roll back file storage. Failed creation attempts
therefore remove only their own generated files after database rollback. Storage
deletion failures are logged without replacing the original error; those files
may require operational cleanup. Process termination can also prevent cleanup.