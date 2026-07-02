class ETLStageAborted(Exception):
    pass


def _is_cleanup_eligible(load_outcome) -> bool:
    cleanup_eligible = getattr(load_outcome, "cleanup_eligible", None)
    if cleanup_eligible is not None:
        return cleanup_eligible

    created_count = getattr(load_outcome, "created_count", None)
    if created_count is not None:
        return created_count > 0

    return bool(load_outcome)


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
    load_outcome,
    garbage_collect,
    enabled: bool,
    threshold_seconds: int,
    logger,
):
    if not enabled:
        logger.info("News garbage collector skipped because it is disabled.")
        return 0

    if not _is_cleanup_eligible(load_outcome):
        logger.info(
            "News garbage collector skipped because the load outcome is not cleanup eligible."
        )
        return 0

    deleted_count = garbage_collect(threshold_seconds=threshold_seconds)
    logger.info(
        "News garbage collector completed.",
        extra={"deleted_count": deleted_count},
    )
    return deleted_count
