import os
import base64
import requests
from datetime import datetime
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration
try:
    GITHUB_USERNAME = st.secrets["github"]["username"]  # Your GitHub username
    GITHUB_TOKEN = st.secrets["github"]["token"]  # Your GitHub personal access token
except KeyError as e:
    st.error(f"Missing secret: {e}")
    st.stop()

GITHUB_REPO = "whiteandbox/cdn"  # Your repo name
TARGET_FOLDER = "testautomated"  # Folder to place the image in the repo
BRANCH_NAME = "main"  # Branch to push the changes

def get_unique_image_name(base_name):
    base_name_without_ext = os.path.splitext(base_name)[0]
    current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
    return f"{base_name_without_ext}_{current_time}.jpg"

def upload_image_to_github(image_path, image_name):
    try:
        logging.info(f"Reading image file: {image_path}")
        with open(image_path, "rb") as image_file:
            content = base64.b64encode(image_file.read()).decode()

        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{TARGET_FOLDER}/{image_name}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "message": f"Add {image_name}",
            "content": content,
            "branch": BRANCH_NAME
        }

        logging.info(f"Uploading image to GitHub: {url}")
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()

        github_file_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH_NAME}/{TARGET_FOLDER}/{image_name}"
        logging.info(f"File uploaded successfully: {github_file_url}")
        return {"status": "success", "url": github_file_url}

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP Request failed: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"status": "error", "message": str(e)}

# Streamlit app
st.title("Image Upload to GitHub")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Ensure the temp directory exists
    if not os.path.exists("temp"):
        os.makedirs("temp")

    # Save the uploaded file temporarily
    temp_image_path = os.path.join("temp", uploaded_file.name)
    with open(temp_image_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Generate unique image name
    unique_image_name = get_unique_image_name(uploaded_file.name)
    logging.info(f"Generated unique image name: {unique_image_name}")

    # Upload the image to GitHub
    response = upload_image_to_github(temp_image_path, unique_image_name)

    # Display the response
    if response["status"] == "success":
        st.success(f"File uploaded successfully: [View Image]({response['url']})")
    else:
        st.error(f"Error: {response['message']}")