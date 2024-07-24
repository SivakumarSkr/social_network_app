---

# Social Network App

This Django Rest Framework (DRF) application serves as a social networking platform where users can sign up, send friend requests to other users, and manage their friends list. The application provides a RESTful API for user interactions and friend management, making it easy to integrate with front-end applications or other services.

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Setup](#setup)
   - [Clone the repository](#clone-the-repository)
   - [Setup Environment Variables](#setup-environment-variables)
   - [Build and Run with Docker Compose](#build-and-run-with-docker-compose)
4. [Usage](#usage)
5. [Endpoints](#endpoints)
6. [Code Formatting and Linting](#code-formatting-and-linting)

## Overview

This project is a social networking platform built with Django and Django Rest Framework (DRF) that allows users to sign up, send friend requests, and manage their friends list. It leverages JSON Web Tokens (JWT) for secure authentication and Docker for containerization to ensure consistent deployment across different environments.

## Requirements

List the prerequisites and dependencies needed to run the project. For example:

- Docker
- Docker Compose
- Python3
- Git

## Setup

### Clone the repository

```bash
git clone https://github.com/SivakumarSkr/social_network_app.git
cd social_network_app
```

### Setup Environment Variables

Copying a `.env.sample` file and modifying it:

```bash
cp .env.sample .env
# Edit .env file with your configurations, such as db details.
```

### Create Virtual environment and Generate SECRET_KEY

Generate a Django secret key using Django's built-in function:

1. Open your terminal and navigate to your Django project directory.
2. Create virtual environment
   ```
   python3 -m venv venv
   ```
3. Activate virtual environment
   ```
   source venv/bin/activate
   ```
4. Install packages
   ```
   pip install -r requirements.txt
   ```
5. Open a python shell by running the following command:

   ```bash
   python
   ```

6. Inside the Django shell, run the following Python commands to generate a new secret key:

   ```python
   from django.core.management.utils import get_random_secret_key;
   print(get_random_secret_key())
   ```

7. The above command will print a new secret key. Copy the generated key.

8. Open your `.env` file and find the `SECRET_KEY` variable. Replace its value with the newly generated secret key:
   ```shell
   SECRET_KEY='your_generated_secret_key_here'
   ```
9. Use this virtual environment for your local coding.

### Build and Run with Docker Compose

```bash
sudo docker compose up --build
```

This command will build the Docker images and start the containers as defined in your `docker-compose.yml`.

## Endpoints

Please find postman collection for endpoints in this [link](https://www.postman.com/technical-explorer-6580566/workspace/my-works/collection/15804981-300b29b4-1cb6-4a55-b576-0d79464cd484?action=share&creator=15804981)

## Code Formatting and Linting

To maintain a clean and consistent codebase, we use Black for code formatting, Flake8 for linting, and MyPy for type checking. Follow these steps to set up and use these tools in your project.

Before running following commands, activate virtual environment.

### 1. Code Formatting with Black

Black is a code formatter that enforces a consistent style. To format your code, run:

```bash
black .
```

This command will format all Python files in your project directory according to Black's style guidelines.

### 2. Linting with Flake8

Flake8 is a tool for checking the style and quality of your code. It helps identify syntax errors, unused variables, and other issues. To lint your code, run:

```bash
flake8 .
```

You can customize Flake8’s behavior by creating a `.flake8` configuration file in the root of your project.

### 3. Type Checking with MyPy

MyPy is a static type checker for Python. It helps ensure that your code adheres to the type hints you’ve provided. To check your code, run:

```bash
mypy .
```

You can customize MyPy’s behavior by creating a `mypy.ini` configuration file in the root of your project.
