# Secure Auth API - FastAPI & Supabase

A secure, containerized RESTful API built with FastAPI that implements robust user authentication. It uses Supabase Auth as the Identity Provider to manage accounts, issue JSON Web Tokens (JWTs), and securely guard protected routes via custom middleware.

## 🏗️ Architecture & Security
* **Backend Framework:** FastAPI (Python 3.10+)
* **Identity Provider:** Supabase Auth
* **Authentication Method:** Stateless JWT (JSON Web Tokens) via Bearer Authorization
* **Containerization:** Docker & Docker Compose

## 🚀 Quick Start Guide

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* A free [Supabase](https://supabase.com/) account.

### 1. Environment Variables
This project requires Supabase API keys to handle authentication. 
Copy the provided example file to create your active `.env` file:
```bash
cp .env.example .env

```

Fill in your `SUPABASE_URL` and `SUPABASE_KEY` (Publishable/anon key) from your Supabase Project Settings.

### 2. Launch the Application

Build and start the containerized server:

```bash
docker compose up --build

```

## 🌐 API Reference

Access the interactive Swagger UI documentation at: **http://localhost:8000/docs**

| Method | Endpoint | Purpose | Auth Required? | Status Codes |
| --- | --- | --- | --- | --- |
| POST | `/auth/signup` | Register a new user account | No | 201, 400 |
| POST | `/auth/login` | Authenticate and return JWT | No | 200, 400, 401 |
| POST | `/auth/logout` | End the user's session | **Yes (Bearer)** | 204, 400 |
| GET | `/public/info` | Open lobby with public data | No | 200 |
| GET | `/protected/profile` | Read private user metadata | **Yes (Bearer)** | 200, 401 |
| GET | `/protected/dashboard` | Access private dashboard | **Yes (Bearer)** | 200, 401 |

## 📸 Screenshots

### 1. Swagger UI - Protected Routes (Bearer Auth)
![padlocks](/Screenshots/padlocks.png)
![Authorize](/Screenshots/fastapiAuthorize.png)

### 2. Successful Token Verification (Profile & Dashboard)
#### Login
![login1](/Screenshots/login1.png)
![login2](/Screenshots/login2.png)

#### Profile & Dashboard
![dashboard](/Screenshots/protectedDashboard.png)
![profile](/Screenshots/protectedProfile.png)

### 3. The Final Push
Once your `.env.example` and `README.md` are saved, run these final commands to publish your secured API to the cloud[cite: 1]:
