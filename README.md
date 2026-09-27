
# Asynchronous Content Distribution Engine & Storage

An asynchronous backend service and content ingestion engine designed for decoupled storage, concurrent request handling, and low-latency relational querying.

## Architecture & Design Decisions

* **Decoupled Storage Pattern:** Relational metadata, session states, and content indexing are strictly partitioned within PostgreSQL, while large binary payloads are offloaded directly to external object storage (Google Drive API) to minimize database footprint.


* **Non-Blocking I/O:** Built on top of Python's `asyncio` event loop to handle concurrent client lookup requests without thread-blocking operations.


* **Relational Integrity & Query Performance:** Normalized PostgreSQL schema with foreign key integrity constraints and structured query filtering for deterministic latency under concurrent read loads.


* **Resilience Layer:** Structured logging, custom session retries for third-party network calls, and automated OAuth token refresh management.



## Tech Stack

* **Core:** Python 3.10+ (asyncio, async HTTP client / Telegram interface)


* **Database:** PostgreSQL


* **Integrations:** Google Drive API (binary payload offloading), Telegram Bot API


* **Environment & Config:** python-dotenv

## Local Setup

1. Clone the repository:
git clone [https://github.com/cocojambo2316/your-repo-name.git](https://www.google.com/search?q=https://github.com/cocojambo2316/your-repo-name.git&utm_source=gemini)
cd your-repo-name
2. Create and activate a virtual environment:
python -m venv .venv
..venv\Scripts\Activate.ps1
3. Install dependencies:
pip install -r requirements.txt
4. Environment Configuration:
Create a .env file in the root directory:
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
GOOGLE_CREDENTIALS_PATH=credentials.json
5. Run the service:
python main.py
