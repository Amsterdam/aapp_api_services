class ETLStageAborted(Exception):
    pass


def _has_created_records(created_records) -> bool:
    created_count = getattr(created_records, "created_count", None)
    if created_count is not None:
        return created_count > 0

    return bool(created_records)


def run_stage(
    *,
    extract,
    extract_empty_message: str,
    transform=None,
    transform_empty_message: str | None = None,
    load=None,
):
    extracted_data = extract()
    if not extracted_data:
        raise ETLStageAborted(extract_empty_message)

    staged_data = extracted_data
    if transform is not None:
        staged_data = transform(extracted_data)
        if not staged_data:
            raise ETLStageAborted(transform_empty_message or extract_empty_message)

    if load is None:
        return staged_data
    return load(staged_data)


def maybe_garbage_collect(
    *,
    created_records,
    garbage_collect,
    enabled: bool,
    threshold_seconds: int,
    logger,
):
    if _has_created_records(created_records) and enabled:
        deleted_count = garbage_collect(threshold_seconds=threshold_seconds)
        logger.info(
            "News garbage collector completed.",
            extra={"deleted_count": deleted_count},
        )
        return deleted_count

    logger.info("News garbage collector skipped because it is disabled.")
    return 0
