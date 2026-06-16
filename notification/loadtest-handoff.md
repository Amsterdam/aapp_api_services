# Device Delete Loadtest Handoff

## Scope

This repository does not contain the loadtest scenarios for the Notification API.
Loadtests for `DELETE /notification/api/v1/device/` are maintained externally.

## Required external scenario updates

1. Include delete calls with known devices that have linked data in:
   - `notification_device`
   - `notification_notification`
   - `notification_schedulednotification` + m2m links
   - `notification_notificationpushtypedisabled`
   - `notification_notificationpushmoduledisabled`
   - `notification_notificationlast`
   - `notification_wastedevice`
   - `notification_burningguidedevice`
2. Include idempotent retries on the same `DeviceId`.
3. Include unknown-device deletes and assert non-blocking success.
4. Include forced backend failure simulation (if supported in the loadtest env) and assert explicit fail contract:
   - HTTP `500`
   - JSON keys: `status`, `error_key`, `message`, `deleted`
   - `status=error`, `error_key=device_delete_failed`, `deleted=false`

## Command/interface expectation

The external runner should execute against the notification service endpoint:

- Method: `DELETE`
- Path: `/notification/api/v1/device/`
- Required header: `DeviceId`
- Auth: API key auth

## Evidence required for sign-off

1. Test execution command and scenario version/hash from external repo.
2. Summary metrics: total requests, p95 latency, error rate.
3. Contract checks proving:
   - successful deletes return explicit success payload
   - retries/unknown devices remain idempotent and non-blocking
   - failure simulation returns explicit fail payload with stable `error_key`
4. Attach logs or report artifact IDs in the work item.