# Changes


## Affected services
- bridge
- city_pass
- construction_work
- contact
- core
- image
- modules
- notification
- survey
- waste

## Definition of done
- [ ] API is backwards compatible (`make openapi-diff`)
- [ ] Swagger UI up-to-date & tested (`make dev`)
- [ ] Dependencies updated (`make requirements`)
- [ ] Infrastructure config updated (aapp_azure_infra)
- [ ] Loadtests for relevant endpoints (aapp_testing_loadtests)

After PR created (and deployed on dev):
- [ ] Manual check on dev (o) e.g. use feature via Swagger or admin panel
- [ ] Sanity check on test app (check that dev environment is selected)

## Other notes

GitHub Copilot was used in writing the code