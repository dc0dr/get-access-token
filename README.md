# 🔑 Get Access Token

A Python automation script that signs into [Microsoft Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) via browser automation, retrieves an access token, and saves it to a specified location on your machine.

## How It Works

The script uses [Playwright](https://playwright.dev/python/) to drive a real Microsoft Edge browser session through the full login flow:

1. **`login_bypass`** — Opens Graph Explorer, clicks "Sign in", and handles the authentication popup. Supports multiple login scenarios:
   - **Microsoft login** — email input, account picker, or "Stay signed in?" prompt
   - **OneLogin SSO** — username/password entry via OneLogin federation
2. **`access_key_scraper`** — Runs the default Graph query and copies the access token from the "Access token" tab.
3. **`file_uploader`** — Writes the token to a local file, copies it to a configured destination directory (e.g. OneDrive), and cleans up the original.

A persistent browser profile (`browser_automation_profile/`) is used so that cached sessions & cookies carry over between runs, reducing how often full credentials are needed.

## Prerequisites

- **Python** ≥ 3.13
- **[uv](https://docs.astral.sh/uv/)** package manager
- **Microsoft Edge** installed locally
- A valid **Microsoft / OneLogin** account with access to Graph Explorer

## Setup

1. **Clone the repository**

   ```bash
   git clone <repo-url>
   cd get-access-token
   ```

2. **Install dependencies**

   ```bash
   uv sync
   ```

3. **Install Playwright browsers**

   ```bash
   uv run playwright install
   ```

4. **Configure environment variables**

   Copy the template and fill in your credentials:

   ```bash
   cp .env.dev .env
   ```

   | Variable          | Description                                                        |
   | ----------------- | ------------------------------------------------------------------ |
   | `EMAIL`           | Your Microsoft / OneLogin email address                            |
   | `PASSWORD`        | Your OneLogin password                                             |
   | `USER_LOCATOR`    | The locator for your user account on the Microsoft login page      |
   | `NAME`            | Your display name as it appears on the Graph Explorer "Sign out" button (e.g. `Emmanuel Daniels`) |
   | `DESTINATION_DIR` | Absolute path where the access token file should be copied to      |

## Usage

```bash
uv run main.py
```

The script will:

1. Launch Edge and navigate to Graph Explorer
2. Automatically sign in (handling Microsoft + OneLogin SSO)
3. Extract the access token
4. Save it to `<DESTINATION_DIR>/access_token.txt`

## Project Structure

```
get-access-token/
├── main.py                 # Entry point — orchestrates the full flow
├── login_bypass.py         # Browser automation for the sign-in sequence
├── access_key_scraper.py   # Extracts the access token from Graph Explorer
├── file_uploader.py        # Writes & copies the token file to destination
├── .env.dev                # Environment variable template
├── pyproject.toml          # Project metadata & dependencies
└── output_files/           # Temporary directory for token file (git-ignored)
```

## Dependencies

| Package        | Purpose                                |
| -------------- | -------------------------------------- |
| `playwright`   | Browser automation (Chromium/Edge)     |
| `python-dotenv`| Load environment variables from `.env` |
| `pyperclip`    | Clipboard utilities                    |
