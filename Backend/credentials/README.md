# Google service account (not in Git)

Place your service account JSON here on each server, for example:

`your-service-account.json`

Set in `Backend/.env`:

```env
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/your-service-account.json
```

**Never commit** `*.json` files from this folder.
