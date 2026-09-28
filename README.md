# AI Lead Assistant

AI-powered lead discovery, qualification, outreach, and pipeline management for small businesses.

## Overview

AI Lead Assistant is a student-built AI application designed to help small businesses find potential customers, evaluate leads, generate personalized outreach, and manage leads through a simple pipeline.

The application combines business discovery, AI analysis, lead qualification, outreach generation, and follow-up planning into one workflow.

## Core Workflow

**Business Target → Business Discovery → AI Relevance Analysis → Lead Qualification → Personalized Outreach → Follow-Up → Pipeline Management**

## Features

### Lead Discovery

* Search for real businesses based on business type and target location
* Uses OpenStreetMap and Overpass API data
* Filters discovered businesses using AI-generated relevance analysis
* Displays business information such as website, phone, address, and industry when available

### AI Lead Qualification

* Generates a lead score from 1–100
* Identifies why a lead may be relevant
* Separates known information from missing information
* Identifies potential business pain points
* Generates qualification questions
* Recommends a next action

### Personalized Outreach

* Generates personalized first-contact messages
* Creates follow-up messages
* Suggests qualification questions
* Recommends the next step in the sales process

### Pipeline Management

Leads can move through:

**New → Contacted → Interested → Meeting → Won → Lost**

The application stores lead information locally using SQLite.

### Business Strategy

Users can enter their business type and goal to generate an AI-assisted strategy covering:

* Ideal customers
* Lead sources
* Outreach methods
* Follow-up strategy
* Qualification questions
* Recommended next actions

## Technology Stack

* **Python**
* **Streamlit**
* **Google Gemini API**
* **SQLite**
* **Requests**
* **OpenStreetMap**
* **Overpass API**

## Architecture

```text
User
  ↓
Streamlit Interface
  ↓
Lead Discovery
  ↓
OpenStreetMap / Overpass API
  ↓
AI Relevance Analysis
  ↓
Lead Qualification
  ↓
Personalized Outreach
  ↓
Follow-Up Planning
  ↓
SQLite Pipeline
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/sidsenthilkumar-dev/AI-Lead-Assistant.git
cd AI-Lead-Assistant
```

### 2. Install dependencies

```bash
pip install streamlit google-genai requests
```

### 3. Add your Gemini API key

Create:

```text
.streamlit/secrets.toml
```

Add:

```toml
GEMINI_API_KEY = "your-api-key-here"
```

**Never commit your API key to GitHub.**

The secrets file is excluded through `.gitignore`.

### 4. Run the application

```bash
streamlit run app.py
```

## Project Status

This project is currently an MVP and is being developed toward a more complete AI-powered lead generation platform.

Current development areas include improving lead discovery, AI qualification, outreach personalization, user experience, and deployment.

## Why I Built It

I wanted to build an AI application that solves a practical business problem rather than only demonstrating a chatbot or basic AI generation.

The goal is to combine APIs, AI, data, and a usable interface into one application that can support a real business workflow.

## Author

**Sid Senthil**

Built as an independent AI/software project.
