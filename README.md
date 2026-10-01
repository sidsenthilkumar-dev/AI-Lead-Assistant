# AI Lead Assistant

An AI-powered tool I built to help small businesses find potential customers, qualify leads, create outreach, and keep track of follow-ups.

## Overview

AI Lead Assistant is a project I built to make the process of finding and managing potential customers easier for small businesses.

The app combines business discovery, AI lead analysis, lead qualification, personalized outreach, and pipeline management into one workflow.

## How It Works

**Business Target → Find Businesses → AI Analysis → Qualify Leads → Create Outreach → Follow Up → Manage Pipeline**

## Features

### Lead Discovery

- Search for real businesses based on business type and location
- Uses OpenStreetMap and the Overpass API to find businesses
- Uses AI to help determine which businesses may be relevant
- Shows information like website, phone number, address, and industry when available

### AI Lead Qualification

- Gives leads a score from 1–100
- Explains why a business could be a good lead
- Separates information that is known from information that is missing
- Identifies possible business problems
- Creates questions that can be used to qualify a lead
- Suggests what to do next

### Personalized Outreach

- Creates personalized first-contact messages
- Generates follow-up messages
- Suggests questions to ask potential customers
- Helps decide what the next step should be

### Pipeline Management

Leads can move through different stages:

**New → Contacted → Interested → Meeting → Won → Lost**

Lead information is stored locally using SQLite.

### Business Strategy

Users can enter their business type and goal to get an AI-generated strategy with things like:

- Ideal customers
- Possible lead sources
- Outreach ideas
- Follow-up strategy
- Qualification questions
- Recommended next steps

## Technology

- **Python**
- **Streamlit**
- **Google Gemini API**
- **SQLite**
- **Requests**
- **OpenStreetMap**
- **Overpass API**

## How the App Works

```text
User
  ↓
Streamlit Interface
  ↓
Find Businesses
  ↓
OpenStreetMap / Overpass API
  ↓
AI Analysis
  ↓
Lead Qualification
  ↓
Personalized Outreach
  ↓
Follow-Up
  ↓
SQLite Lead Pipeline
