# Orchestrating SQL Workflows with Apache Airflow and Trino

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://opensource.org/licenses/MIT)

This project demonstrates how to use **Apache Airflow** to orchestrate, schedule, and monitor complex SQL workflows executed on a **Trino** distributed query engine. The entire environment is containerized using **Docker Compose**, providing a portable and reproducible setup for building robust data pipelines.

The core of this project involves setting up an Airflow instance, integrating it with a Trino service, and deploying a custom DAG (Directed Acyclic Graph) that runs a series of dependent and parallel SQL queries.

## Table of Contents

1.  [Key Features](#key-features)
2.  [System Architecture](#system-architecture)
3.  [Technology Stack](#technology-stack)
4.  [Getting Started: Environment Setup](#getting-started-environment-setup)
    -   [Prerequisites](#prerequisites)
    -   [Step 1: Initialize the Airflow Environment](#step-1-initialize-the-airflow-environment)
    -   [Step 2: Customize the Docker Compose File](#step-2-customize-the-docker-compose-file)
    -   [Step 3: Launch the Services](#step-3-launch-the-services)
    -   [Step 4: Install the Airflow Trino Provider](#step-4-install-the-airflow-trino-provider)
5.  [Project Configuration and Deployment](#project-configuration-and-deployment)
    -   [Step 1: Access the Airflow Web UI](#step-1-access-the-airflow-web-ui)
    -   [Step 2: Configure the Trino Connection](#step-2-configure-the-trino-connection)
    -   [Step 3: Deploy the Custom TrinoOperator](#step-3-deploy-the-custom-trinooperator)
    -   [Step 4: Deploy the Example DAG](#step-4-deploy-the-example-dag)
    -   [Step 5: Run and Monitor the DAG](#step-5-run-and-monitor-the-dag)
6.  [Understanding the Custom `TrinoOperator`](#understanding-the-custom-trinooperator)
7.  [Shutting Down the Environment](#shutting-down-the-environment)

## Key Features

-   **Workflow as Code:** Define complex data pipelines dynamically using Python.
-   **Distributed SQL Execution:** Leverage Trino to run high-performance queries against large datasets from various sources.
-   **Containerized Setup:** All components (Airflow, Trino, Postgres, Redis) run in Docker containers for easy setup and consistency.
-   **Custom Operator:** Includes a custom `TrinoOperator` that can handle single or multiple semicolon-separated SQL statements in a single task.
-   **Task Dependency Management:** Demonstrates how to define complex dependencies, including sequential and parallel task execution (`task1 >> task2 >> [task3, task4]`).
-   **Centralized Monitoring:** Use the Airflow UI to schedule, trigger, monitor, and debug workflows.

## System Architecture

The workflow is orchestrated as follows:

1.  **Docker Compose** launches the entire stack:
    -   **Airflow Services:** Webserver, Scheduler, Worker, Flower (for monitoring).
    -   **Airflow Backend:** A PostgreSQL database for metadata and Redis for the Celery queue.
    -   **Trino Service:** A single-node Trino coordinator for executing SQL queries.
2.  The **Airflow Scheduler** periodically scans the `dags` folder, parses the Python DAG file, and determines the schedule and task dependencies.
3.  When a DAG run is triggered (either manually or by the schedule), the Scheduler places the first tasks into the **Redis** queue.
4.  An **Airflow Worker** picks up a task from the queue.
5.  If the task is a `TrinoOperator` task, the worker uses the pre-configured Trino connection details to establish a connection with the **Trino** service.
6.  The operator sends the SQL query to Trino for execution.
7.  The status of the query is monitored, and upon completion, the task's status is updated in the Airflow metadata database.
8.  The entire process is visible and manageable through the **Airflow Web UI**.

## Technology Stack

| Component               | Technology                                             | Role                                                      |
| ----------------------- | ------------------------------------------------------ | --------------------------------------------------------- |
| **Orchestration**       | Apache Airflow                                         | Scheduling, executing, and monitoring workflows.          |
| **Query Engine**        | Trino                                                  | High-performance, distributed SQL query engine.           |
| **Airflow Backend**     | PostgreSQL                                             | Stores Airflow metadata (DAGs, task instances, etc.).     |
| **Message Broker**      | Redis                                                  | Message broker for the Celery Executor in Airflow.        |
| **Containerization**    | Docker & Docker Compose                                | Manages the multi-container environment and networking.   |

## Getting Started: Environment Setup

### Prerequisites

-   **Docker** and **Docker Compose:** Must be installed and running on your local machine.
-   **cURL:** A command-line tool for downloading files.

### Step 1: Initialize the Airflow Environment

First, fetch the official Docker Compose file from the Apache Airflow project and create the necessary directories.

```bash
# Download the official docker-compose.yaml file
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'

# Create directories for DAGs, logs, and plugins
mkdir -p ./dags ./logs ./plugins

# Create the .env file and set the Airflow User ID to the current user
echo -e "AIRFLOW_UID=$(id -u)" > .env
```

### Step 2: Customize the Docker Compose File

We need to add the Trino service to our environment. Open the `docker-compose.yaml` file you just downloaded and add the following service definition under the `services:` block.

```yaml
  trino:
    image: trinodb/trino
    container_name: trino
    ports:
      - "8081:8080"
```
*Tip: A good place to add this is right after the `redis:` service definition.*

### Step 3: Launch the Services

Start all the containers in detached mode.

```bash
docker-compose up -d
```
The first launch may take several minutes as Docker needs to download all the required images.
<img width="638" height="184" alt="image" src="https://github.com/user-attachments/assets/95c7d932-e4b7-457f-8958-edff2e7e555f" />


### Step 4: Install the Airflow Trino Provider

Once the containers are running, you need to install the official Trino provider package into the Airflow worker and scheduler containers.

```bash
# Find your scheduler and worker container names
docker ps

# Install the provider on the scheduler
docker exec -it <your-airflow-scheduler-container-name> pip install apache-airflow-providers-trino

# Install the provider on the worker
docker exec -it <your-airflow-worker-container-name> pip install apache-airflow-providers-trino
```
<img width="614" height="32" alt="image" src="https://github.com/user-attachments/assets/bfcc290e-c283-46e0-879c-497878bd3ac9" />

> **Permission Denied?** If you encounter a permission error, it's because the `pip` command is being run as root. Use the `airflow` user instead with the full path to its local pip binary:
> ```bash
> docker exec -it --user airflow <container_name> /home/airflow/.local/bin/pip install apache-airflow-providers-trino
> ```

After installing the provider, **restart the containers** for the changes to take effect:
```bash
docker-compose restart scheduler worker webserver
```

## Project Configuration and Deployment

### Step 1: Access the Airflow Web UI

Open your browser and navigate to **[http://localhost:8080](http://localhost:8080)**.
Log in with the default credentials:
-   **Username:** `airflow`
-   **Password:** `airflow`

### Step 2: Configure the Trino Connection

In the Airflow UI, you need to tell Airflow how to connect to your Trino instance.

1.  Navigate to **Admin -> Connections**.
2.  Click the `+` button to add a new record.
3.  Fill in the form with the following details:
    -   **Connection Id:** `asa123456` (This must match the `trino_conn_id` used in the DAG).
    -   **Connection Type:** `Trino`
    -   **Host:** `trino` (The service name from `docker-compose.yaml`).
    -   **Port:** `8080`
4.  Click **Save**.
<img width="694" height="495" alt="image" src="https://github.com/user-attachments/assets/3fe937e7-eca7-4b9b-9961-dda8d347e333" />

### Step 3: Deploy the Custom TrinoOperator

Create a new file named `trino_operator.py` inside the `plugins` directory you created earlier. Copy the Python code for the `TrinoCustomHook` and `TrinoOperator` classes from the project documentation into this file.

Airflow will automatically detect and load any code placed in the `plugins` folder. You may need to wait a minute or two for the scheduler to pick it up.

### Step 4: Deploy the Example DAG

Create a new Python file inside the `dags` directory (e.g., `trino_pipeline_dag.py`). Copy the complete DAG code from the project documentation into this file.

### Step 5: Run and Monitor the DAG

1.  Go back to the Airflow UI and navigate to the **DAGs** page.
2.  After a minute, your new DAG, `akif_trino_scheduled_job`, should appear in the list.
3.  Click the toggle button to un-pause the DAG.
4.  To run it immediately, click the "Play" button on the right-hand side and select "Trigger DAG".
5.  Click on the DAG name to view its progress in the Graph, Gantt, and Grid views. You can click on individual tasks to view their logs and see the output from Trino.

<img width="1132" height="643" alt="image" src="https://github.com/user-attachments/assets/72bbc71c-6af0-4432-a004-523b70685292" />

<img width="1041" height="768" alt="image" src="https://github.com/user-attachments/assets/cf271095-f126-4307-9c2f-926a52b50d55" />

<img width="1077" height="774" alt="image" src="https://github.com/user-attachments/assets/86d44d23-6baa-4a24-b79e-48f55a7ee4ed" />

<img width="1070" height="431" alt="image" src="https://github.com/user-attachments/assets/db2b5171-c3d1-4de5-8da4-cc34f9857e50" />


## Understanding the Custom `TrinoOperator`

The custom `TrinoOperator` provided in this project extends Airflow's `BaseOperator`. Its primary feature is the ability to intelligently handle SQL code. In the `execute` method, it checks if the provided `sql` parameter is a single statement or a string containing multiple statements separated by semicolons (`;`).

-   If it's a **single statement**, it executes it efficiently using `hook.get_first()`.
-   If it's a **multi-statement string**, it splits the string into a list of individual statements and executes them sequentially within a single Trino session using `hook.run()`.

This provides greater flexibility for defining tasks that need to perform a series of setup and execution steps within a single transaction or session.

## Shutting Down the Environment

To stop and remove all the containers, networks, and volumes, run the following command from the project's root directory:

```bash
docker-compose down -v
```
> **Warning:** The `-v` flag will delete the Docker volumes, which includes the PostgreSQL database storing all your Airflow metadata. Omit this flag if you want to preserve your DAG run history and connections.
