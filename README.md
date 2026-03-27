# 📇 Contact Manager API

A high-performance RESTful API for contact management, built with **FastAPI**. The project follows a robust layered architecture (**Controller -> Service -> Repository**), ensuring that business logic, data persistence, and entry interfaces are completely decoupled and testable.

---

## 🏗️ Design Patterns & Architecture

- **App Factory Pattern:** The application is instantiated via a `create_app()` function, facilitating configuration across different environments (development, testing, production) and allowing for a clean initialization of middlewares and routes.
- **Layered Architecture:** Clear separation between the transport layer (Controllers), business logic (Services), and data access (Repositories).
- **Dependency Injection:** Extensive use of FastAPI's dependency injection system to manage database sessions and service lifetimes.

---

## 📂 Project Structure

The code organization reflects the **Separation of Concerns** principle:

```text
.
├── app
│   ├── config          # DB, JWT, and Environment configurations
│   ├── controllers     # Endpoints and input validation (HTTP Layer)
│   ├── errors          # Exception handlers and custom error responses
│   ├── models          # SQLAlchemy Models (Database definitions)
│   ├── repositories    # Data persistence and queries (Data Access Layer)
│   ├── schemas         # DTOs and data validation (Pydantic v2)
│   └── services        # Business logic and orchestration (Business Layer)
├── tests               # Test suite (Unit and Integration)
├── pyproject.toml      # Dependency management and Taskipy scripts
└── run.py              # Application Entry Point
```

---

## ⚡ Asynchronous Architecture & Performance

The project is designed to be **non-blocking** from end-to-end:

- **Async I/O:** Powered by `SQLAlchemy 2.0` with the `ext.asyncio` extension and the `aiosqlite` driver, ensuring that database operations do not block the _Event Loop_.
- **CPU-Bound Offloading:** Intensive tasks, such as password hashing with `bcrypt`, are delegated to separate threads via `asyncio.to_thread`. This keeps the API responsive even under heavy authentication loads.

---

## 🛠️ Technology Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous focus).
- **Database:** SQLite (via `aiosqlite` for async support).
- **ORM:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/).
- **Security:** `python-jose` (JWT), `bcrypt` (Hashing), `SlowAPI` (Rate Limiting).
- **Tooling:** `Ruff` (Linter/Formatter), `Taskipy` (Task Runner), `Poetry`.

---

## 🔐 Security & Middlewares

- **JWT Authentication:** Dual token system (`access` and `refresh`).
- **Ownership Control:** The `owner_required` dependency ensures data isolation: a user can never access or modify another user's resources.
- **Security Headers:** Custom middleware injecting:
  - **CSP (Content Security Policy):** Specifically configured to allow only necessary assets for Swagger UI while blocking everything else (`default-src 'none'`).
  - **HSTS, X-Content-Type-Options, and X-Frame-Options** for protection against common web vulnerabilities.
- **Rate Limiting:** Active brute-force protection on critical endpoints.

---

## 🧪 Testing Strategy (~90% Coverage)

System reliability is guaranteed by three testing levels using **Pytest**:

1.  **Unit Tests (Controllers):** Tests route behavior in isolation using _Mocks_ for the Service layer.
2.  **Unit Tests (Services):** Validates isolated business rules using _Mocks_ for the Repository layer.
3.  **Integration Tests (Repository/API):** Full-flow tests using an **in-memory SQLite** database.

---

## 🚀 How to Run

### 1. Prerequisites

- Python 3.14+
- Poetry

### 2. Setup

```bash
# Install dependencies
poetry install

# Environment setup - Fill in the required variables
cp .env.example .env
```

### 3. Useful Commands (via Taskipy)

| Command                  | Description                                            |
| :----------------------- | :----------------------------------------------------- |
| `poetry run task run`    | Starts the server in development mode (`fastapi dev`). |
| `poetry run task test`   | Runs the test suite with a coverage report.            |
| `poetry run task lint`   | Runs static code analysis with **Ruff**.               |
| `poetry run task format` | Automatically formats the code.                        |

---

## 📍 Key Endpoints

The full interactive documentation (**Swagger UI**) is available at `/swagger`.

| Method | Endpoint                | Auth/Protection | Description                       |
| :----- | :---------------------- | :-------------- | :-------------------------------- |
| POST   | `/users/`               | Public          | Register a new user.              |
| POST   | `/users/login`          | Public          | Authenticate and generate tokens. |
| GET    | `/users/refresh`        | Refresh Token   | Renew access token.               |
| GET    | `/users/{id}/contacts/` | JWT + Owner     | List user's contacts.             |
| POST   | `/users/{id}/contacts/` | JWT + Owner     | Create a new contact.             |

---

## 📄 License

Distributed under the MIT License.

---

## 🌟 Support & Contact

If this project helped you or you found it interesting, please **leave a star (⭐)** on the repository! It greatly helps the project's visibility.

**Developed by Diego Godoi** 📧 **Email:** diegogodoimartins.11@gmail.com
