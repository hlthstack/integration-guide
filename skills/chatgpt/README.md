# hlthstack custom GPT

Set up a ChatGPT custom GPT that can explain and call the hlthstack API.

## Steps

1. In ChatGPT, open **Explore GPTs** -> **Create** -> **Configure**.
2. **Name**: `hlthstack API assistant`. **Description**: "Helps integrate with and call the
   hlthstack health-benefits API."
3. **Instructions**: paste the contents of [`instructions.md`](instructions.md).
4. **Knowledge** (optional): upload the files in [`../../docs/`](../../docs/) so the GPT can
   quote the guides.
5. **Actions** -> **Create new action**:
   - **Schema**: import from URL
     `https://raw.githubusercontent.com/hlthstack/integration-guide/main/openapi/openapi.yaml`,
     or paste the file's contents.
   - The spec lists production first. To use staging, move the
     `https://staging-api.hlthstack.io` server to the top of `servers` (or delete the
     production entry) in the pasted schema. Use staging while testing.
   - **Authentication**: choose **API Key** -> **Bearer**, and paste an access token from
     `GET /api/get-access-token`. Tokens expire after 1 hour, so update the key when it
     stops working. Don't give the GPT your API username and password.
   - Optionally remove operations you don't want the GPT to call (for example the `Testing`
     tag, or create/cancel operations for a read-only assistant). Custom GPT actions only
     use one server and don't call webhooks.
6. **Privacy policy**: required by ChatGPT when actions are enabled; use your own policy URL.
7. Save, and choose who can access the GPT. Keep it private if the action key is set: anyone
   using the GPT acts with that token.

## Notes

- Multi-entity partners: GPT actions can't add the `API-ENTITY-ID` / `API-SECRET-KEY`
  headers per call safely; use a token for a single-entity setup, or don't use actions.
- The GPT should ask before creating, rescheduling or cancelling bookings or orders (this is
  in the instructions).
