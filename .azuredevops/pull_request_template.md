Affected services
- core
- bridge
- city_pass
- construction_work
- contact
- modules
- waste
- image
- notification
- survey

Definition of Done:
- [ ] API is backwards compatible (`make openapi-diff`)
- [ ] Swagger UI up-to-date & tested (`make dev`)
- [ ] Dependencies updated (`make requirements`)
- [ ] Unittest coverage >90% (`make coverage`)
- [ ] Infrastructure config updated (aapp_azure_infra)
- [ ] Loadtests for relevant endpoints (aapp_testing_loadtests)

If manually deployed:
- [ ] Manual check on dev (o) & test (t), e.g. use feature via Swagger or admin panel
- [ ] Sanity check on test app
