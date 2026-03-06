# Local Lead Prospector (B2B Lead Generator)

## 📌 About The Project

**Local Lead Prospector** is a powerful, automated tool designed to streamline the process of finding and prospecting B2B clients for Web Development and Local SEO services.

Finding quality leads manually is a time-consuming and tedious process. This project was built to completely automate lead generation, business auditing, and outreach email drafting to significantly save time and boost sales efficiency.

## ✨ Key Features

- **Interactive Map Search**: Fast and intuitive lead discovery using an interactive map powered by Leaflet and Google Places API (New).
- **Kanban Board (Drag & Drop)**: Built-in mini-CRM visualizing your sales pipeline with status columns (New, To Contact, Contacted, Rejected, Closed).
- **Comprehensive Business Auditor**: An automated site auditor tracking essential metrics:
    - Security (SSL checks)
    - Responsiveness (RWD / Mobile-friendly)
    - Page Load Speed
    - Basic SEO Tags
    - Google Business Profile Analysis
- **AI Integration (Gemini 2.5 Flash)**: Connects to the newest Gemini models to instantly analyze audit reports and generate highly personalized, intelligent sales emails ready to be sent to prospects.

## 🛠️ Tech Stack

### Frontend

- **Vue 3** (Composition API)
- **Tailwind CSS**
- **Vite**

### Backend

- **FastAPI**
- **Python**
- **SQLite**
- **BeautifulSoup**

### DevOps

- **Docker & Docker Compose**
- **Nginx**

## 🔑 Environment Variables

To run this project, you will need to add the following environment variables. Create a `.env` file in your `backend` directory based on this structure:

```env
# backend/.env

GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

## 🚀 Getting Started

There are two ways to run this project. For the most foolproof and guaranteed working environment, we recommend using Docker.

### Method A: Docker (Recommended)

1. Make sure you have Docker and Docker Compose installed.
2. Ensure your `backend/.env` file is properly configured.
3. Open your terminal in the root directory and run the following command:

```bash
docker-compose up --build
```

- The Frontend will be available at `http://localhost:80` (or `http://localhost`)
- The Backend / API documentation will be available at `http://localhost:8000/docs`

---

### Method B: Manual (For Developers)

If you wish to run the app natively for development without Docker, follow these steps:

#### 1. Setup Backend

Open a terminal and navigate to the backend folder:

```bash
cd backend
```

Create and activate a virtual environment:

**On Linux/macOS:**

```bash
python -m venv venv
source venv/bin/activate
```

**On Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Start the FastAPI development server:

```bash
uvicorn main:app --reload
```

_The API will be running on `http://127.0.0.1:8000`_

#### 2. Setup Frontend

Open a **new** terminal window and navigate to the frontend folder:

```bash
cd frontend
```

Install Node.js dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

_The frontend application will be running on a local port (usually `http://localhost:5173`)_
