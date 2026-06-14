# Job Search Tracker

A lightweight, self-hosted dashboard for tracking job applications — companies, positions, and statuses — with a neo-brutalist UI and a tiny Flask backend that persists everything to a local JSON file.

## Features

- Track companies with multiple positions/applications nested underneath
- Update application status as you progress through interviews
- Data saved to `jobs.json` on disk via a simple Flask API

## Running locally

```bash
pip install flask
python3 server.py
```

Then open http://localhost:5200 in your browser.
