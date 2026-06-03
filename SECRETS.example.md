# Files to copy to a new PC (not in Git)

Copy these from your **working computer** to the same paths after `git clone`:

```
Backend/.env
Backend/credentials/e-commerce-data-domnak-*.json   (if using Google Sheets backup)
```

## Minimum fields in `Backend/.env`

| Variable | Notes |
|----------|--------|
| `POSTGRES_PASSWORD` | Same as in `DATABASE_URL` |
| `DATABASE_URL` | Host must be `db` for Docker |
| `JWT_SECRET_KEY` | Long random string |
| `TELEGRAM_BOT_TOKEN` | Same token = same bot (one poller only) |
| `TELEGRAM_CHAT_ID` | Your chat / group id |
| `GOOGLE_SHEET_ID` | If backup enabled |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path under `credentials/` |

Do **not** commit these files to GitHub.

Full guide: [docs/DEPLOY-NEW-PC.md](docs/DEPLOY-NEW-PC.md)
