## Plan: Afvalscheidingswijzer Proxy

Add a minimal authenticated Bridge endpoint that accepts a raw text/plain POST body from clients, forwards that body unchanged to the configured upstream Afvalscheidingswijzer URL with the required fixed headers, and returns the upstream body unchanged with its original content type. This should reuse the existing bridge/proxy view-and-url conventions, but prefer an HttpResponse passthrough instead of DRF JSON serialization because the sample upstream response is a streamed text format, not JSON.

**Steps**
1. Add a dedicated POST-only GenericAPIView in bridge/proxy/views.py for the new endpoint. It should read request.body directly instead of request.data so text/plain requests work without JSON parsing.
2. In that view, call requests.post to settings.AFVALSCHEIDINGSWIJZER_URL with timeout, body=request.body, and fixed upstream headers: content-type text/plain;charset=UTF-8, next-action 40f8fc5dcb243472b32eb5cb1040d8e6e896f79498, origin https://www.afvalscheidingswijzer.nl, user-agent Mozilla/5.0. Do not forward arbitrary client headers upstream for this first version.
3. Return the upstream response as a plain HttpResponse using response.content, response.status_code, and response.headers["Content-Type"] when present. This keeps the non-JSON upstream payload intact and matches the existing raw passthrough pattern already used by AddressSearchView in bridge/proxy/views.py.
4. Add focused upstream error handling in the same view. Catch requests.exceptions.RequestException and return a small JSON error body with HTTP 502, following the existing proxy module convention used by AddressSearchAbstractView for upstream failures. Avoid broader retry logic or caching for this story.
5. Register the route in bridge/proxy/urls.py as bridge/api/v1/afvalscheidingswijzer with name afvalscheidingswijzer. Keep it alongside the other bridge-scoped utility endpoints.
6. Add or update schema decoration in bridge/proxy/views.py so the contract is explicit in OpenAPI: request body is text/plain string payload, method is POST only, and success response is raw string/binary passthrough rather than JSON object transformation. Prefer drf-spectacular annotations in the view over adding a JSON serializer, because the request body is intentionally unstructured text.
7. Extend bridge/proxy/tests/test_proxy_views.py with focused tests for: successful POST passthrough, exact upstream URL/method, exact required upstream headers, unchanged raw request body, propagated upstream status, propagated response body, and propagated response content type.
8. Add one failure test in bridge/proxy/tests/test_proxy_views.py that makes requests.post raise a RequestException and asserts Bridge returns 502 with a stable error payload. If the implementation chooses to guard against non-POST methods explicitly, add the default 405 expectation rather than custom handling.

**Relevant files**
- bridge/proxy/views.py — add the new Afvalscheidingswijzer proxy view; reuse AddressSearchView as the raw-response passthrough reference and AddressSearchAbstractView as the local 502 error-handling reference.
- bridge/proxy/urls.py — register the new public endpoint path and route name.
- bridge/proxy/tests/test_proxy_views.py — add the new endpoint tests using the existing ResponsesActivatedAPITestCase pattern.
- bridge/proxy/tests/mock_data.py — reuse the existing AFVALSCHEIDINGSWIJZER sample response constant already added by the user.
- bridge/settings/base.py — reuse the existing AFVALSCHEIDINGSWIJZER_URL setting already added by the user; no settings change should be needed.
- .bruno-workspace/collections/Extern/Afvalscheidingswijzer.yml — use as the exact upstream header/body example while implementing and verifying the request contract.

**Verification**
1. Run the focused bridge proxy tests covering the new view in bridge/proxy/tests/test_proxy_views.py and confirm both the success path and the 502 upstream-failure path pass.
2. In the success test, assert the recorded upstream call received the raw body ["potgrond"] and the hardcoded headers exactly as specified in the Bruno example.
3. In the success test, assert the Bridge response body equals mock_data.AFVALSCHEIDINGSWIJZER and that the response Content-Type matches the mocked upstream header instead of being coerced into JSON.
4. Confirm non-POST requests are not accepted by the endpoint via default GenericAPIView method handling if the route exposes only post().

**Decisions**
- Response handling: proxy through raw bytes/text, not transformed JSON. Reason: the provided upstream sample is not valid JSON and existing bridge/proxy code already uses HttpResponse when preserving upstream content matters.
- Request handling: accept plain text payload exactly as received and forward request.body unchanged. Reason: the story explicitly says the client request data is plain text.
- Header handling: hardcode the upstream next-action value and the other required browser-like headers for now; do not make them configurable in this story.
- Scope boundary: only the new endpoint, targeted OpenAPI annotation, and focused view tests are included. No caching, retries, reusable proxy base class refactor, auth changes, or response parsing are included.

**Further Considerations**
1. Assumption to keep implementation unblocked: the public Bridge route is bridge/api/v1/afvalscheidingswijzer and uses the existing API key authentication inherited from GenericAPIView defaults in this app.
2. If drf-spectacular cannot express the raw text request cleanly with the current helper utilities, document the request/response shape directly on the view with extend_schema and OpenApiTypes rather than introducing a misleading serializer.
