import os
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# =========================
# PATH SETUP
# =========================

# Absolute path to project root (parent of src/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =========================
# CONFIGURATION
# =========================

# Input CSV containing vocabulary and example data
INPUT_CSV = os.path.join(BASE_DIR, "data", "input", "danish_vocab_input.csv")

# Folder to store downloaded HTML pages (cache)
HTML_DIR = os.path.join(BASE_DIR, "cache", "html_pages")

# Folder to store generated CSV outputs
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# Anki media folder where audio files must be saved
AUDIO_DIR = os.path.expanduser(
    "~/Library/Application Support/Anki2/User 1/collection.media"
)

# Base URL for ordnet.dk dictionary lookups
BASE_URL = "https://ordnet.dk/ddo/ordbog?query="

# Ensure required directories exist
os.makedirs(HTML_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


# =========================
# UTILITY FUNCTIONS
# =========================


def clean_word(word):
    """
    Normalize a word so it is safe for URLs and filenames.
    Keeps Danish characters and removes punctuation.
    """
    return re.sub(
        r"[^a-zA-Z\u00C0-\u024F\u1E00-\u1EFFæøåÆØÅ]",
        "",
        word.lower(),
    )


def setup_driver():
    """
    Create a headless Chrome Selenium driver.
    Selenium automatically manages the correct ChromeDriver version.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920x1080")
    service = Service()
    return webdriver.Chrome(service=service, options=chrome_options)


# =========================
# SCRAPING FUNCTIONS
# =========================


def save_html(driver, word):
    """
    Load the dictionary page for a word and save the full HTML locally.
    """
    try:
        url = BASE_URL + word
        driver.get(url)
        time.sleep(3)

        file_path = os.path.join(HTML_DIR, f"{word}.html")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        print(f"✓ Saved HTML for: {word}")

    except Exception as e:
        print(f"❌ Failed to save HTML for {word}: {e}")


def extract_audio_url(word):
    """
    Parse a saved HTML file and extract the MP3 pronunciation URL.
    """
    filepath = os.path.join(HTML_DIR, f"{word}.html")
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    for img in soup.find_all("img", src=True):
        if "speaker.gif" in img["src"]:
            onclick = img.get("onclick", "")
            match = re.search(r"playSound\('(.*?)'\)", onclick)
            if match:
                sound_id = match.group(1)
                fallback = soup.find("a", id=f"{sound_id}_fallback")
                if fallback and fallback.get("href", "").endswith(".mp3"):
                    return fallback["href"]

    return None


# =========================
# AUDIO HANDLING
# =========================


def download_audio_file(url, audio_dir, word):
    """
    Download the audio file and save it as <word>.mp3
    Returns the filename for later Anki reference.
    """
    if not url or not url.endswith(".mp3"):
        return ""

    filename = f"{word}.mp3"
    output_path = os.path.join(audio_dir, filename)

    if os.path.exists(output_path):
        print(f"⏩ Skipped (already exists): {filename}")
        return filename

    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"🎧 Downloaded: {filename}")
            return filename
        else:
            print(f"⚠️ Failed to download {url}")
            return ""

    except Exception as e:
        print(f"❌ Error downloading audio from {url}: {e}")
        return ""


# =========================
# MAIN PIPELINE
# =========================


def main():
    """
    Full pipeline:
    CSV → scrape HTML → extract audio → download audio
    → generate Anki-ready CSV files
    """

    df = pd.read_csv(INPUT_CSV, encoding="utf-8-sig", sep=";")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)

    driver = setup_driver()
    results = []

    for word in df["Word"]:
        clean = clean_word(str(word))

        html_path = os.path.join(HTML_DIR, f"{clean}.html")
        if not os.path.exists(html_path):
            save_html(driver, clean)

        audio_url = extract_audio_url(clean)
        audio_filename = ""

        if audio_url:
            audio_filename = download_audio_file(audio_url, AUDIO_DIR, clean)

        results.append(
            {
                "Word": word,
                "AudioFilename": audio_filename,
            }
        )

    driver.quit()

    audio_df = pd.DataFrame(results)
    df_merged = df.merge(audio_df, on="Word", how="left")

    df_merged["Audio"] = "[sound:" + df_merged["AudioFilename"].fillna("") + "]"

    df_merged["Danish Sentence"] = (
        df_merged["Example Sentence (Danish)"].astype(str).str.strip()
    )
    df_merged["Meaning"] = df_merged["Meaning"].astype(str).str.strip()
    df_merged["English Translation"] = (
        df_merged["Example Translation (English)"].astype(str).str.strip()
    )
    df_merged["Forms"] = df_merged["Forms"].astype(str).fillna("").str.strip()

    structured = df_merged[
        ["Word", "Audio", "Danish Sentence", "Meaning", "English Translation", "Forms"]
    ]
    structured.to_csv(
        os.path.join(OUTPUT_DIR, "anki_cards_structured.csv"),
        sep=";",
        index=False,
    )

    df_merged["Front"] = (
        "<b>"
        + df_merged["Word"]
        + "</b><br>"
        + df_merged["Audio"]
        + "<br>"
        + df_merged["Danish Sentence"]
    )

    df_merged["Back"] = (
        df_merged["Meaning"]
        + "<br>"
        + "<span style='color:gray;'>"
        + df_merged["English Translation"]
        + "</span><br>"
        + "<i><b>Forms:</b> "
        + df_merged["Forms"]
        + "</i>"
    )

    ready = df_merged[["Front", "Back"]]
    ready.to_csv(
        os.path.join(OUTPUT_DIR, "anki_cards_ready.csv"),
        sep=";",
        index=False,
    )

    print("✨ Anki CSV files generated successfully.")


if __name__ == "__main__":
    main()
