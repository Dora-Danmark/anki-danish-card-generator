# Anki Danish Card Generator

Generate Anki flashcards with Danish pronunciation audio using data from ordnet.dk.

This project takes a CSV file with Danish vocabulary and example sentences, downloads official pronunciation audio, and outputs Anki-ready CSV files.

---

## Features

- Automatically fetches Danish pronunciation audio from ordnet.dk
- Saves audio files directly into Anki's media folder
- Generates clean, Anki-importable CSV files
- Uses a clear and scalable project structure
- Designed for Danish PD2 / PD3 vocabulary learning

---

## Project Structure
"""
anki-danish-card-generator/
├── src/
│ └── anki_danish_card_generator.py
├── data/
│ ├── input/
│ │ └── danish_vocab_input.csv
│ └── output/
│ ├── anki_cards_structured.csv
│ └── anki_cards_ready.csv
├── cache/
│ └── html_pages/
├── requirements.txt
├── .gitignore
└── README.md
"""

---

## Input CSV Format

The input file must be a semicolon-separated CSV with the following columns:

| Column name | Description |
|------------|------------|
| Word | Danish word |
| Example Sentence (Danish) | Example sentence in Danish |
| Meaning | English meaning |
| Example Translation (English) | English translation |
| Forms | Grammatical forms |


---

## Requirements

- Python 3.10 or newer
- Google Chrome installed
- Anki installed (desktop)

Python dependencies:
pandas
requests
beautifulsoup4
selenium




