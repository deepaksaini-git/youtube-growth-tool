# YouTube Growth Toolkit v2

Features:
- Authorized channel analytics: daily views, estimated watch time, average view duration, subscribers gained
- Topic research from public YouTube search results and public video statistics
- Template-based SEO title and description drafts
- Thumbnail concept checklist
- Downloadable content calendar CSV

## Deploy from Android using GitHub + Streamlit Community Cloud

1. Extract the ZIP and upload `app.py`, `requirements.txt`, `README.md`, `.gitignore` to a GitHub repository.
2. In https://console.cloud.google.com/ enable **YouTube Analytics API** and **YouTube Data API v3**.
3. Configure Google Auth Platform / OAuth consent screen. If in Testing mode, add your Google account as a test user.
4. Create OAuth Client ID → **Web application**. Add this exact redirect URI after the app is deployed:
   `https://YOUR-APP-NAME.streamlit.app/`
5. Deploy at https://share.streamlit.io/ using repository, branch `main`, and main file `app.py`.
6. In Streamlit app Advanced settings → Secrets, paste this TOML and replace all placeholders:

```toml
[google]
client_id = "YOUR_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "YOUR_GOOGLE_OAUTH_CLIENT_SECRET"
redirect_uri = "https://YOUR-APP-NAME.streamlit.app/"

[youtube_data]
api_key = "YOUR_YOUTUBE_DATA_API_V3_KEY"
```

7. Make sure `redirect_uri` in Streamlit Secrets matches the Authorized redirect URI in Google Cloud exactly, including trailing slash.
8. Get a Data API key from Google Cloud → APIs & Services → Credentials → Create credentials → API key. Restrict it to **YouTube Data API v3** and put it only in Streamlit Secrets, never in GitHub.
9. Use **Connect Google / reconnect** in the app and authorize the channel you manage.

## Security and limitations
- Never commit API keys, OAuth secrets, tokens, or private exports.
- The starter keeps OAuth credentials in Streamlit session state; refreshing or starting a new session may require reconnecting. It is not a production multi-user token-storage system.
- Topic research uses public search results and public video counts. It does not predict virality or show private competitor analytics.
- SEO helper is template-based and does not measure search volume.
- Thumbnail tab gives concepts, not a rendered thumbnail image.
- Keep the app private while testing. Review OAuth consent and verification requirements before public multi-user use.
- No fake views, automated playback, or guaranteed growth.
