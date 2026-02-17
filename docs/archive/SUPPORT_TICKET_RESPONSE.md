# Support Ticket Response for Best.Energy

Hi Alex,

Thanks for your guidance. I've now tested the key-only authentication approach you recommended, but I'm still getting errors. Here's what I've found:

## Tests Performed

**Test 1: API Key Only (Your Recommended Approach)**
```bash
curl "https://core.eniscope.com/api?action=summarize&apikey=REDACTED&id=23271"
```
**Result**: `HTTP/2 403 Forbidden` (empty body)

**Test 2: With Full Parameters**
```bash
curl "https://core.eniscope.com/api?action=summarize&apikey=REDACTED&id=23271&res=900&range_start=2025-04-29%2000:00:00&range_end=2025-04-29%2023:59:59&format=json"
```
**Result**: `HTTP/2 403 Forbidden` (empty body)

**Test 3: Python requests library (same params)**
**Result**: `401 Unauthorized` or `403 Forbidden` depending on headers

## Key Observations

1. The API key is being accepted by the server (not getting invalid key errors)
2. However, all requests are being rejected with **403 Forbidden**, suggesting a **permissions issue**
3. Per your earlier message, you asked: "Could you confirm if the user craig@argoenergysolutions.com has **'API Access'** specifically enabled in their user permissions?"

## Questions

1. **Can you verify that our API key has "API Access" permission enabled?**
   - Is there a specific permission flag that needs to be set on the API key itself?

2. **Does my user account (craig@argoenergysolutions.com) have the correct role/permissions?**
   - What specific permissions are required to use the API with an API key?

3. **Is there a different endpoint or action I should be using?**
   - Should I be using `/api`, `/readings`, or another endpoint?
   - Is `action=summarize` the correct action for pulling historical data?

4. **Can you check server logs for this API key?**
   - When I make requests with our API key
   - What error/rejection reason is being logged?

5. **Should I regenerate the API key?**
   - If I generate a new API key, are there specific settings I need to enable?

## What I'm Trying to Do

I need to pull 15-minute interval energy data for Org 23271 from April 29, 2025 onwards. Previously I could access data from November onwards, but now I can only see data from April 29 onwards in the web portal.

I want to use the API to:
- Fetch readings for all channels in the organization
- Use `action=summarize` with 900-second resolution
- Store the data in our PostgreSQL database for analytics

## Environment

- API Key: (see .env — do not commit to version control)
- Organization ID: 23271
- User: craig@argoenergysolutions.com
- Endpoint: https://core.eniscope.com/api

Thanks for your help troubleshooting this!

Craig Argo
Argo Energy Solutions
