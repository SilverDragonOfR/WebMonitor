# Uptime Monitor with Discord Notifications

## Project Overview

This project is a streamlined service designed to monitor website availability and promptly notify users of status changes via Discord webhooks.  It periodically checks website health, tracks historical uptime and downtime, and alerts users upon site outages or recoveries. Built for clarity, robustness, and ease of use, it balances core monitoring needs with practical features for real-world application.

## Setup Instructions

To get the Uptime Monitor running on your local machine, follow these steps:

1.  **Clone the Repository:**

    Begin by cloning the project repository from GitHub to your local environment:

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Install Dependencies:**

    The project dependencies are managed using pip (recommended) or Python Poetry. Choose your preferred method to install them:

    *   **Using pip (Recommended):**

        If you prefer pip, use the `requirements.txt` file:

        ```bash
        pip install -r requirements.txt
        ```

    *   **Using Poetry:**

        Alternately, If you have Poetry installed, simply run:

        ```bash
        poetry install
        ```


3.  **Configure Environment Variables:**

    Create a `.env` file in the root directory of the project. This file will hold your configuration settings. Add the following variables, adjusting the values as needed:

    ```env
    VALID_USERNAME=<user name for authentication>
    VALID_PASSWORD=<password for authentication>
    REDIS_URL=<redis server url (not for Docker)>
    DATABASE_URL=<sqlite database url>
    RATE_LIMIT=<requests per window per user>
    RATE_WINDOW=<window size in sec>
    OPTIMISATION=<whether database optimisation is done>
    DEFAULT_TIMEOUT_SECONDS=<timeout for status check>
    ```

    *   `REDIS_URL`:  The address of your Redis server.  `redis://localhost:6379/0` works for local Redis with default settings.
    *   `DATABASE_URL`:  Specifies the database connection. SQLite is default (`sqlite:///./web_monitor.db`). For other databases like PostgreSQL or MySQL, modify this URL accordingly.
    *   `VALID_USERNAME`, `VALID_PASSWORD`:  Credentials for HTTP Basic Authentication to secure the API. Set your desired username and password.
    *   `OPTIMISATION`:  Either 0 (not done) or 1 (done) for Database efficiency.
    *   `DEFAULT_TIMEOUT_SECONDS`: Sets the default timeout (in seconds) for website check requests.

4.  **Initialize the virtual env (Both in Celery terminal & Server terminal):**

    Run Celery and Uvicorn server *both* in venv:

    ```bash
    python -m venv venv
    ./venv/Scripts/Activate.ps1
    ```

5.  **Start the Celery Worker:**

    Open a **new terminal window** and start the Celery worker. This process handles the background website monitoring tasks. Run:

    ```bash
    celery -A app.background_worker worker --loglevel=info -P gevent
    ```

6.  **Start the FastAPI Application:**

    Open **another new terminal window** and launch the FastAPI application server. This runs the API that you will interact with. Execute:

    ```bash
    python main.py
    ```

7.  **Access API Documentation:**

    Once the FastAPI application is up and running, you can explore the interactive API documentation in your browser:

    *   **Swagger UI:**  Navigate to `http://localhost:8000/docs`
    *   **ReDoc:** Navigate to `http://localhost:8000/redoc`

    Use these interfaces to understand the available API endpoints, request structures, response formats, and to test API calls directly.

## API Documentation

The API uses HTTP Basic Authentication for security. Remember to include your configured `USERNAME` and `PASSWORD` in the `Authorization` header for all requests.

**1. Site Management Endpoints:**

*   **POST `/sites`**:  Endpoint to add a new website to be monitored.

    *   **Method:** `POST`
    *   **URL:** `/sites`
    *   **Request Body (JSON):**
        ```json
        {
            "url": "https://example.com/",
            "name": "Example Site",
            "check_interval_seconds": 60,
            "expected_status_code": 200
        }
        ```
    *   **Successful Response (200 OK):**
        ```json
        {
            "url": "https://example.com/",
            "name": "Example Site",
            "check_interval_seconds": 60,
            "expected_status_code": 200,
            "id": 1
        }
        ```
    *   **Error Response (400 Bad Request):**
        ```json
        { "detail": "Invalid URL" }
        ```

*   **DELETE `/sites/{site_id}`**: Endpoint to remove a website from monitoring.

    *   **Method:** `DELETE`
    *   **URL:** `/sites/{site_id}`  (Replace `{site_id}` with the actual site ID)
    *   **Path Parameter:** `site_id` (integer) - ID of the site to delete.
    *   **Successful Response (200 OK):**
        ```json
        { "detail": "Site deleted successfully" }
        ```
    *   **Error Response (400 Bad Request):**
        ```json
        { "detail": "Site not found" }
        ```

*   **GET `/sites/{site_id}`** - Endpoint to get details of a specific monitored website by its ID.

    *   **Method:** `GET`
    *   **URL:** `/sites/{site_id}` (Replace `{site_id}` with the actual site ID)
    *   **Path Parameter:** `site_id` (integer) - The ID of the site to retrieve.
    *   **Request Body:** None
    *   **Successful Response (200 OK):**
        ```json
        {
            "url": "https://example.com/",
            "name": "Example Website",
            "check_interval_seconds": 60,
            "expected_status_code": 200,
            "id": 1
        }
        ```
    *   **Error Response (400 Bad Request):**
        ```json
        {
          "detail": "Site not found"
        }
        ```

*   **GET `/sites`**: Endpoint to retrieve a list of all monitored websites.

    *   **Method:** `GET`
    *   **URL:** `/sites`
    *   **Request Body:** None
    *   **Successful Response (200 OK):**
        ```json
        [
            {
                "url": "https://example.com/",
                "name": "Example Site",
                "check_interval_seconds": 60,
                "expected_status_code": 200,
                "id": 1
            },
            {
                "url": "https://another-site.com/",
                "name": "Another Site",
                "check_interval_seconds": 300,
                "expected_status_code": 200,
                "id": 2
            }
        ]
        ```

*   **GET `/sites/{site_id}/history`**: Endpoint to fetch the status history for a specific website.

    *   **Method:** `GET`
    *   **URL:** `/sites/{site_id}/history` (Replace `{site_id}` with the actual site ID)
    *   **Path Parameter:** `site_id` (integer) - ID of the site to get history for.
    *   **Successful Response (200 OK):**
        ```json
        [
            {
                "status": "INITIAL",
                "response_time_ms": null,
                "last_checked": "2025-02-15T06:30:00.000Z",
                "last_status_change": "2025-02-15T06:30:00.000Z"
            },
            {
                "status": "UP",
                "response_time_ms": 150,
                "last_checked": "2025-02-15T06:35:00.000Z",
                "last_status_change": "2025-02-15T06:35:00.000Z"
            },
            {
                "status": "DOWN",
                "response_time_ms": null,
                "last_checked": "2025-02-15T06:40:00.000Z",
                "last_status_change": "2025-02-15T06:40:00.000Z"
            }
        ]
        ```
    *   **Error Response (400 Bad Request):**
        ```json
        { "detail": "Site not found" }
        ```

**2. Webhook Configuration Endpoints:**

*   **POST `/webhooks`**: Endpoint to configure a Discord webhook for a monitored website.

    *   **Method:** `POST`
    *   **URL:** `/webhooks`
    *   **Request Body (JSON):**
        ```json
        {
            "site_id": 1,
            "discord_webhook_url": "your_discord_webhook_url"
        }
        ```
    *   **Successful Response (200 OK):**
        ```json
        {
            "site_id": 1,
            "discord_webhook_url": "your_discord_webhook_url",
            "id": 1
        }
        ```
    *   **Error Response (400 Bad Request):**
        ```json
        { "detail": "Site not found" }
        ```

*   **DELETE `/webhooks/{webhook_id}`**: Endpoint to delete a specific webhook configuration.

    *   **Method:** `DELETE`
    *   **URL:** `/webhooks/{webhook_id}` (Replace `{webhook_id}` with the actual webhook ID)
    *   **Path Parameter:** `webhook_id` (integer) - ID of the webhook to delete.
    *   **Successful Response (200 OK):**
        ```json
        { "detail": "Webhook deleted successfully" }
        ```
    *   **Error Response (400 Bad Request):**
        ```json
        { "detail": "Webhook not found" }
        ```

*   **GET `/webhooks/{site_id}`**: Endpoint to retrieve all webhooks configured for a specific website.

    *   **Method:** `GET`
    *   **URL:** `/webhooks/{site_id}` (Replace `{site_id}` with the actual site ID)
    *   **Path Parameter:** `site_id` (integer) - ID of the site to get webhooks for.
    *   **Successful Response (200 OK):**
        ```json
        [
            {
                "site_id": 1,
                "discord_webhook_url": "your_discord_webhook_url_1",
                "id": 1
            },
            {
                "site_id": 1,
                "discord_webhook_url": "your_discord_webhook_url_2",
                "id": 2
            }
        ]
        ```
     *   **Error Response (400 Bad Request):**
        ```json
        { "detail": "Site not found" }
        ```

*   **GET `/webhooks/{site_id}`** - Endpoint to get all Discord webhooks configured for a specific website ID.

    *   **Method:** `GET`
    *   **URL:** `/webhooks/{site_id}` (Replace `{site_id}` with the actual site ID)
    *   **Path Parameter:** `site_id` (integer) - The ID of the site to retrieve webhooks for.
    *   **Request Body:** None
    *   **Successful Response (200 OK):**
        ```json
        [
            {
                "site_id": 1,
                "discord_webhook_url": "your_discord_webhook_url_1",
                "id": 1
            },
            {
                "site_id": 1,
                "discord_webhook_url": "your_discord_webhook_url_2",
                "id": 2
            }
        ]
        ```
    *   **Error Response (400 Bad Request):**
        ```json
        {
          "detail": "Site not found"
        }
        ```

*   **GET `/webhooks`**: Endpoint to retrieve all configured webhooks across all websites.

    *   **Method:** `GET`
    *   **URL:** `/webhooks`
    *   **Request Body:** None
    *   **Successful Response (200 OK):**
        ```json
        [
            {
                "site_id": 1,
                "discord_webhook_url": "your_discord_webhook_url_1",
                "id": 1
            },
            {
                "site_id": 2,
                "discord_webhook_url": "your_discord_webhook_url_2",
                "id": 2
            }
        ]
        ```

## Architecture and Code Flow

The Uptime Monitor is structured using a layered architecture to ensure separation of concerns and maintainability. Here's a breakdown of the key components and how they interact:

1.  **API Layer (FastAPI - `app.run.app`):**
    *   **Entry Point:**  FastAPI handles all incoming HTTP requests to the API endpoints.
    *   **Request Handling:**  API routes are defined in `app/run.py` and `app/sites.py`. FastAPI manages routing, request parsing, and response generation.
    *   **Input Validation:** Pydantic models are used to define request and response data structures, providing automatic validation of incoming data (e.g., URL format, data types).
    *   **Authentication:** HTTP Basic Authentication is enforced for all API endpoints using a dependency (`app.auth.get_current_user`).
    *   **Data Serialization:** FastAPI automatically serializes responses into JSON format based on the defined Pydantic response models.
    *   **Interaction with other layers:** The API layer interacts with the CRUD layer (`app.crud`) to perform database operations and triggers background tasks via Celery (`app.background_worker.celery_app.send_task`).

2.  **Background Task Layer (Celery - `app.background_worker.celery_app`):**
    *   **Task Definition:**  Celery tasks are defined in `app/background_worker.py` (e.g., `check_website_status`, `send_discord_notification`).
    *   **Task Triggering:** The monitoring cycle is initiated programmatically by `apply_async`.  The application's code is designed to periodically trigger the website status checks.
    *   **Task Iteration:**  The monitoring process iterates through all monitored sites stored in the database.
    *   **Task Enqueueing:** For each site, it enqueues a `check_website_status` task to Celery using `apply_async`. This immediately sends the task to the Celery task queue.
    *   **Celery Worker Execution:** A Celery worker process picks up the `check_website_status` task from the queue and begins processing it.
    *   **Website Status Checking:** The `check_website_status` task performs an HTTP GET request to the website URL.
    *   **Status Determination:** It determines the website status (up or down) based on the HTTP response and compares it to the `expected_status_code`.
    *   **Status History Retrieval:** The task retrieves the previous status of the website from the database to detect status changes.
    *   **Status Change Handling:**
        *   **Status Changed:** If the website's status has changed (e.g., from "up" to "down" or vice versa), the task updates the `SiteStatusHistory` in the database with the new status and timestamp. It then enqueues `send_discord_notification` tasks to Celery for each webhook configured for the site, to send out alerts.
        *   **Status Unchanged:** If the website's status remains the same, the task still updates the `SiteStatusHistory` with the new `last_checked` timestamp.  An optimization is in place (controlled by `database_optisation` flag) to avoid writing to the database if the status is unchanged and optimization is enabled, reducing unnecessary database operations.


3.  **Data Access Layer (SQLAlchemy - `app.database`, `app.models`):**
    *   **Database Models:** SQLAlchemy models (`app.models.Site`, `app.models.Webhook`, `app.models.SiteStatusHistory`) define the database schema and represent data entities.
    *   **Database Interaction:** SQLAlchemy ORM handles all database interactions, abstracting away raw SQL queries.
    *   **Database Session Management:**  Database sessions are managed using dependency injection (`app.sites.get_db`), ensuring proper session creation and closing for each request or task.
    *   **CRUD Operations:**  The `app.crud` module provides functions for common database operations (Create, Read, Update, Delete) on the models, used by both the API and background tasks.

4.  **Notification Layer (`app.notification.discord_notification`):**
    *   **Discord Notification Logic:**  The `send_discord_notification` function in `app/notification/discord_notification.py` encapsulates the logic for sending messages to Discord webhooks.
    *   **Error Handling:**  This layer includes error handling for potential issues with sending Discord notifications (e.g., network errors, invalid webhook URLs).

**Flow of Control:**

1.  **Adding a Website:**
    *   User sends a `POST /sites` request to the API with website details.
    *   FastAPI API layer validates the request data using Pydantic models.
    *   The API layer calls the CRUD layer (`app.crud.create_site`) to store the new site in the database.
    *   FastAPI returns a success response with the created site details.

2.  **Website Monitoring (Background Task):**
    *   Celery periodically triggers the `check_website_status` task.
    *   This task iterates through all monitored sites in the database.
    *   For each site, it enqueues the `check_website_status` task to Celery.
    *   Celery worker picks up the `check_website_status` task.
    *   `check_website_status` performs an HTTP GET request to the website URL.
    *   It determines the website status (up or down) based on the response.
    *   It retrieves the previous status from the database.
    *   If the status has changed, it updates the `SiteStatusHistory` in the database and enqueues `send_discord_notification` tasks for configured webhooks.
    *   If the status has not changed, it updates `SiteStatusHistory` with new `last_checked` timestamp (optimized to avoid write if `database_optisation` is enabled and no status change).

3.  **Discord Notification (Background Task):**
    *   Celery worker picks up a `send_discord_notification` task.
    *   `send_discord_notification` retrieves the Discord webhook URL and notification message from the task arguments.
    *   It sends an HTTP POST request to the Discord webhook URL with the notification message.
    *   Error handling is in place to log any failures in sending notifications.

4.  **Retrieving Site History:**
    *   User sends a `GET /sites/{site_id}/history` request to the API.
    *   FastAPI API layer validates the request and extracts the `site_id`.
    *   The API layer calls the CRUD layer (`app.crud.get_site_history`) to fetch the status history from the database.
    *   FastAPI returns a success response with the status history data in JSON format.

## Implemented Features

This Uptime Monitor effectively addresses the core requirements and incorporates valuable enhancements:

**Core Requirements:**

*   **Website Monitoring Management:**
    *   **Solution:** REST API endpoints (`POST /sites`, `DELETE /sites/{id}`, `GET /sites`, `GET /sites/{id}/history`) provide full CRUD operations for managing monitored websites.
*   **Configurable Check Intervals:**
    *   **Solution:**  The `check_interval_seconds` field in the `Site` model and API allows setting custom check intervals per website, defaulting to 5 minutes (300 seconds).
*   **HTTP Status Checks:**
    *   **Solution:**  Background Celery tasks perform HTTP GET requests to monitor website status, verifying against the `expected_status_code` (defaulting to 200).
*   **Uptime/Downtime History Tracking:**
    *   **Solution:**  The `SiteStatusHistory` model and associated database table store a history of website status checks, including timestamps, status, and response times, accessible via the `GET /sites/{site_id}/history` endpoint.
*   **Framework Used:**
    *   **Solution:** FastAPI was selected as the framework due to its *high performance, ease of development, and automatic data validation*. Its asynchronous capabilities are well-suited for handling API requests efficiently, and its built-in OpenAPI documentation simplifies API understanding and testing.
*   **Background Task Monitoring Tool:**
    *   **Solution:** Celery is employed as the background task queue for website monitoring due to its *robustness, scalability, and mature ecosystem*. Celery allows for reliable offloading of monitoring tasks, ensuring API responsiveness and the ability to scale the number of monitored sites. **Redis** is used as the message broker for Celery.
*   **Discord Integration for Notifications:**
    *   **Solution:**  Discord webhook URLs are configurable via the `POST /webhooks` API. The system sends notifications for "Website Down" and "Website Recovery" events, including "Website Monitoring started" and "Website Monitoring ended" scenarios.

**Bonus Features:**

*   **Multiple Discord Webhooks:**
    *   **Solution:**  The system allows associating multiple Discord webhook URLs with a single monitored website, enabling notifications to be sent to different Discord channels based on the site or notification type.
*   **Basic Authentication for API Security:**
    *   **Solution:**  HTTP Basic Authentication is implemented for all API endpoints, securing access to site and webhook management functionalities, controlled by `USERNAME` and `PASSWORD` environment variables.
*   **Retry Logic for Robust Checks:**
    *   **Solution:**  Retry logic using the `tenacity` library is implemented in the `check_website_status` task. Transient network errors are handled by retrying website checks before declaring a site as down, reducing false alerts.

**Extra Features & Optimizations:**

*   **Database Write Optimization:**
    *   **Solution:**  The `database_optisation` flag in the `check_website_status` task minimizes database writes by only updating the `last_status_change` timestamp when a genuine status transition occurs.
*   **Clear Discord Notification Formatting:**
    *   **Solution:**  Discord notifications are formatted for readability, including site name, URL, status (UP/DOWN), timestamp, and downtime duration (for recovery alerts).
*   **Comprehensive Test Suite:**
    *   **Solution:**  A pytest-based integration test suite covers core monitoring logic, API endpoints, and database interactions, ensuring system stability and functionality.

## Future Improvements

This uptime monitoring service can be further enhanced with a range of features to improve its functionality, scalability, and user experience. Here are some key areas for future development:

*   **Enhanced Health Checks:**
    *   Implement checks beyond simple HTTP GET requests, such as:
        *   Content verification to ensure specific text or elements are present on the page.
        *   Performance monitoring to track response times and alert on slow websites.
        *   Support for various HTTP methods (POST, HEAD, etc.) for more complex interactions.
        *   TCP port monitoring to check the availability of other services beyond web servers.
*   **Advanced Status History:**
    *   Implement pagination for the status history API to efficiently handle large datasets.
    *   Add filtering and sorting options to the history API (e.g., by status, date range).
    *   Consider visualizing status history with charts or dashboards for better trend analysis.
*   **Notification System Enhancements:**
    *   Expand notification channels to include email, Slack, SMS, or other messaging platforms.
    *   Allow users to customize notification templates for different alert types.
    *   Implement notification throttling or grouping to manage alert frequency and prevent overload.
    *   Enable configurable notification triggers (e.g., alert only after a sustained number of failed checks).
*   **User Interface (UI):**
    *   Develop a web-based UI to simplify management of monitored sites and webhooks.
    *   Include features in the UI to view real-time status, access history, and configure settings.
*   **Metrics and Monitoring:**
    *   Integrate with monitoring and metrics tools like Prometheus and Grafana to expose service performance metrics.
    *   Monitor task queue length, worker performance, and API latency for operational insights.
*   **Database Management:**
    *   Implement database migrations using Alembic to manage database schema changes in a controlled and versioned manner, facilitating easier updates and collaboration.
*   **Security Enhancements:**
    *   Replace Basic Authentication with more robust security mechanisms like OAuth 2.0 or JWT for production environments.
    *   Implement role-based access control (RBAC) to manage user permissions and access to API endpoints.

## Docker Integration

This project includes Docker configuration for easy deployment and containerization. Docker simplifies setup, ensures consistent environments, and streamlines deployment processes.

**Services Defined in `docker-compose.yml`:**

The `docker-compose.yml` file defines three services essential for running the Uptime Monitor:

*   **`web` (webmonitor-web):**
    *   This service runs the FastAPI application server, which handles API requests and user interactions.
    *   It's built from the provided `Dockerfile` in the project context.
    *   Port `8000` on the container is mapped to port `8000` on the host, making the API accessible at `http://localhost:8000`.
    *   It depends on the `redis` and `worker` services, ensuring they are running before the web application starts.
    *   Environment variables are configured to manage API authentication, Redis connection, database URL, rate limiting, optimization settings, and default timeout.

*   **`worker` (webmonitor-worker):**
    *   This service runs the Celery worker process, responsible for executing background tasks like website status checks and sending notifications.
    *   It's also built from the `Dockerfile`.
    *   It depends on the `redis` service.
    *   It uses the same environment variables as the `web` service to ensure consistent configuration.

*   **`redis` (webmonitor-redis):**
    *   This service runs a Redis server using the official `redis:latest` Docker image.
    *   Port `6379` on the container is mapped to port `6379` on the host, allowing communication with the Celery worker and web application.
    *   It serves as the message broker for Celery, managing the task queue.

**Running the Application with Docker Compose:**

1.  **Ensure Docker and Docker Compose are installed:**  Make sure you have Docker and Docker Compose installed on your system. Follow the official Docker documentation for installation instructions for your operating system.

2.  **Navigate to the project directory:** Open your terminal and navigate to the root directory of the Uptime Monitor project, where the `docker-compose.yml` and `Dockerfile` are located.

3.  **Start the services:** Run the following command in your terminal to start all services defined in `docker-compose.yml`:

    ```bash
    docker-compose up --build
    ```

    *   `docker-compose up`:  This command starts all services defined in the `docker-compose.yml` file.
    *   `--build`: This flag ensures that the Docker images for the `web` and `worker` services are built from the `Dockerfile` if they don't exist or if the `Dockerfile` has changed.

5.  **Access the API:** Once the services are running, the FastAPI API will be accessible at `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs` and `http://localhost:8000/redoc`.

6.  **Stop the services:** To stop the Docker Compose services, run:

    ```bash
    docker-compose down
    ```

    This command gracefully stops and removes the containers, networks, and volumes created by `docker-compose up`.