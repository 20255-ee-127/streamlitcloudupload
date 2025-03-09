import os
import base64
import requests
from datetime import datetime
import streamlit as st

# Configuration
try:
    GITHUB_USERNAME = st.secrets["github"]["username"]  # Your GitHub username
    GITHUB_TOKEN = st.secrets["github"]["token"]  # Your GitHub personal access token
except KeyError as e:
    st.error(f"Missing secret: {e}")
    st.stop()

GITHUB_REPO = "whiteandbox/cdn"  # Your repo name
TARGET_FOLDER = "testautomated"  # Folder to place the image in the repo
BRANCH_NAME = "dummy"  # Branch to push the changes

def get_unique_image_name(base_name):
    current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
    return f"{base_name}_{current_time}.jpg"

def upload_image_to_github(image_path, image_name):
    try:
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

        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()

        github_file_url = response.json()["content"]["html_url"]
        print(f"File uploaded successfully: {github_file_url}")
        return {"status": "success", "url": github_file_url}

    except Exception as e:
        print(f"Error: {e}")
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

    # Upload the image to GitHub
    response = upload_image_to_github(temp_image_path, unique_image_name)

    # Display the response
    if response["status"] == "success":
        st.success(f"File uploaded successfully: [View Image]({response['url']})")
    else:
        st.error(f"Error: {response['message']}")