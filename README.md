<div align="center">

# 🤖 AI Multilingual Telegram Bot

### A powerful multilingual Telegram AI assistant with coding, chat, multiple AI models, and advanced admin controls.

<p>
  <img src="https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Telethon-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white">
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white">
  <img src="https://img.shields.io/badge/AsyncIO-Asynchronous-2C2C2C?style=for-the-badge">
</p>

<br>

**Developed by Ehsan Fazli**

</div>

---

## ✨ Overview

**AI Multilingual Telegram Bot** is an asynchronous Telegram AI assistant built with Python and Telethon.

The bot provides two main experiences:

* 💬 General AI conversations
* 🧑‍💻 AI-powered code generation

Users can select their preferred interface language, programming language, and AI model. The bot also includes an administration panel, user management, broadcast messaging, and mandatory channel membership.

---

## 🚀 Features

### 🤖 AI Features

* 💬 AI chat mode
* 🧑‍💻 Programming assistant
* 🧠 Multiple AI model support
* 🔄 Retry previous coding requests
* 🌍 Multilingual interface
* ⚡ Asynchronous API communication

### 🧑‍💻 Coding Mode

Supported programming languages include:

`Python` · `Java` · `JavaScript` · `C#` · `C++` · `Swift` · `Golang` · `Rust` · `Kotlin` · `TypeScript` · `PHP` · `Ruby` · `SQL` · `Shell` · `MATLAB` · `VHDL` · `Solidity` · `Delphi` · `R` · `Elixir` · `Lua`

The bot automatically:

1. Detects whether the request is programming-related.
2. Sends the request to the selected AI model.
3. Generates code for the selected language.
4. Formats the result for Telegram.
5. Sends long responses as downloadable files.

---

## 🧠 Supported AI Models

The bot currently supports multiple model providers and model families, including:

| Model            | Provider   |
| ---------------- | ---------- |
| GPT-4            | GPT API    |
| Qwen2.5 Coder    | Llama API  |
| Arcee AI         | Llama API  |
| Llama 4 Maverick | Llama API  |
| Llama 4 Scout    | Llama API  |
| Llama 3 70B      | Llama API  |
| Llama 3 8B       | Llama API  |
| Mixtral          | Llama API  |
| Gemma            | Llama API  |
| DeepSeek V3      | Llama API  |
| DeepSeek R1      | Llama API  |
| Gemini 1.5 Flash | Gemini API |
| Gemini 1.5 Pro   | Gemini API |
| Gemini 2.0 Flash | Gemini API |
| Gemini 2.5 Pro   | Gemini API |

The default model is:

```text
GPT-4
```

---

## 🌍 Multilingual Interface

The interface currently supports:

🇮🇷 **Persian**

🇬🇧 **English**

Users can change the interface language directly from the Settings menu.

---

## ⚙️ User Features

Each user has an independent configuration including:

* 🌐 Interface language
* 🧠 Selected AI model
* 💻 Selected programming language
* 💬 Chat state
* 🔄 Last coding request

User preferences are persisted using SQLite.

---

## 🔒 Mandatory Channel Membership

The bot includes a configurable **Forced Join System**.

Administrators can:

* ➕ Add channels
* ➖ Remove channels
* 📋 View required channels
* ✅ Verify user membership
* 🔐 Require users to join channels before using the bot

Example flow:

```text
User starts bot
       ↓
Check required channels
       ↓
 ┌───────────────┐
 │ Joined all?   │
 └───────┬───────┘
         │
    ┌────┴────┐
   YES        NO
    │          │
    ↓          ↓
 Main Bot   Join Channels
               ↓
          Verify Membership
```

---

## 👑 Admin Panel

The administrator has access to a dedicated management panel.

### Available Controls

* 🟢 Enable / disable bot
* 📢 Broadcast messages
* 👥 View registered users
* 🔒 Manage forced channels
* ➕ Add mandatory channels
* ➖ Remove mandatory channels
* 📋 List mandatory channels

The admin panel is protected by a numeric Telegram user ID.

---

## 🗄️ Database

The project uses **SQLite** with `aiosqlite`.

### Main Tables

```text
users
├── user_id
├── username
├── first_name
├── ui_lang
├── selected_ai_model
└── last_seen

forced_channels
├── channel_id
├── channel_username
└── channel_title

user_joined_channels
├── user_id
├── channel_id
└── joined_at
```

---

## 🛠️ Tech Stack

<div align="center">

| Technology | Purpose                |
| ---------- | ---------------------- |
| Python     | Core application       |
| Telethon   | Telegram client        |
| aiohttp    | Async HTTP requests    |
| aiosqlite  | Async SQLite database  |
| asyncio    | Asynchronous execution |
| Requests   | HTTP utilities         |
| JSON       | API communication      |

</div>

---

## 📦 Installation

Clone the repository:

```bash
git clone https://github.com/TssHack/your-repository.git
cd your-repository
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Example `requirements.txt`:

```text
telethon
aiosqlite
aiohttp
requests
```

---

## 🔧 Configuration

Before running the bot, configure your Telegram API credentials:

```python
api_id = YOUR_API_ID
api_hash = "YOUR_API_HASH"

admin_id = YOUR_ADMIN_ID

session_name = "my_ai_multilang"
db_file = "users_data.db"
```

Then configure your AI API endpoints:

```python
GPT4_API_URL = "YOUR_GPT_API"
LAMA_API_URL = "YOUR_LAMA_API"
GEMINI_API_URL = "YOUR_GEMINI_API"
```

> ⚠️ Never commit your Telegram API credentials, bot tokens, private API keys, or session files to a public repository.

---

## ▶️ Run

Start the bot with:

```bash
python index.py
```

On the first run, Telethon may ask you to authenticate your Telegram account.

After successful authentication:

```text
Database initialized.
Starting bot...
Bot started successfully.
Bot is running...
```

---

## 📱 Bot Commands

| Command  | Description                 |
| -------- | --------------------------- |
| `/start` | Start the bot               |
| `/admin` | Open administrator panel    |
| `/panel` | Open forced-join management |

---

## 🧩 Project Architecture

```text
Telegram User
      │
      ▼
   Telethon
      │
      ▼
 Message Handler
      │
      ├───────────────┐
      │               │
      ▼               ▼
 Coding Mode       Chat Mode
      │               │
      ▼               ▼
 Request Validation   AI Request
      │               │
      └───────┬───────┘
              ▼
        Selected AI Model
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
    GPT-4   Llama    Gemini
      │       │        │
      └───────┼────────┘
              ▼
          Response
              │
              ▼
          Telegram
```

---

## 🔐 Security Notes

For production deployments, move sensitive configuration into environment variables.

Example:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
ADMIN_ID=your_admin_id

GPT4_API_URL=your_api_url
LAMA_API_URL=your_api_url
GEMINI_API_URL=your_api_url
```

Avoid committing:

```text
*.session
*.db
.env
__pycache__/
```

---

## 📈 Future Improvements

Possible improvements for future versions:

* [ ] Environment-based configuration
* [ ] PostgreSQL support
* [ ] Redis-based user state
* [ ] Better membership verification
* [ ] AI conversation history
* [ ] Streaming AI responses
* [ ] Usage statistics
* [ ] Rate limiting
* [ ] Per-user request limits
* [ ] Admin analytics dashboard
* [ ] Docker support
* [ ] Web-based administration panel

---

## 👨‍💻 Author

<div align="center">

### Ehsan Fazli

**Full Stack Developer · Open Source Enthusiast**

<br>

🌐 **Website**

[https://ehsanfazli.ir](https://ehsanfazli.ir)

<br>

💼 **LinkedIn**

[https://linkedin.com/in/ehsanfazliii](https://linkedin.com/in/ehsanfazliii)

<br>

📧 **Email**

[ehsanfazlinejad@gmail.com](mailto:ehsanfazlinejad@gmail.com)

</div>

---

<div align="center">

### ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub.

<br>

**Built with Python 🐍 and Telethon ❤️**

<br>

© 2026 **Ehsan Fazli**

</div>
