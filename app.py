import os
import git
from datetime import datetime
import streamlit as st

# Configuration
try:
    GITHUB_USERNAME = st.secrets["github"]["username"]  # Your GitHub username
    GITHUB_TOKEN = st.secrets["github"]["token"]  # Your GitHub personal access token
except KeyError as e:
    st.error(f"Missing secret: {e}")
    st.stop()

GITHUB_REPO = "https://github.com/whiteandbox/codebase.git"  # Your repo HTTPS URL
LOCAL_REPO_PATH = "codebase"  # Path to the local cloned repo
TARGET_FOLDER = "testautomated"  # Folder to place the image in the repo
BRANCH_NAME = "dummy"  # Branch to push the changes

def get_unique_image_name(base_path, base_name):
    counter = 1
    unique_name = base_name
    while os.path.exists(os.path.join(base_path, unique_name)):
        unique_name = f"{base_name}_{counter}"
        counter += 1
    return unique_name

def clone_repository():
    retries = 3
    for attempt in range(retries):
        try:
            print("Cloning repository...")
            git.Repo.clone_from(
                f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@github.com/whiteandbox/codebase.git",
                LOCAL_REPO_PATH,
                config='http.postBuffer=524288000'
            )
            return True
        except Exception as e:
            print(f"Clone attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(5)  # Wait for 5 seconds before retrying
            else:
                return False

def commit_and_push_image(image_path):
    try:
        # Ensure the local repo exists
        if not os.path.exists(LOCAL_REPO_PATH):
            if not clone_repository():
                return {"status": "error", "message": "Failed to clone repository after multiple attempts"}

        repo = git.Repo(LOCAL_REPO_PATH)

        # Ensure the target folder exists in the repo
        target_folder_path = os.path.join(LOCAL_REPO_PATH, TARGET_FOLDER)
        if not os.path.exists(target_folder_path):
            os.makedirs(target_folder_path)

        # Generate unique image name with current date and timestamp
        current_time = datetime.now().strftime("%d%m%Y_%H%M%S")
        base_image_name = f"{current_time}.jpg"
        unique_image_name = get_unique_image_name(target_folder_path, base_image_name)

        # Copy image to target folder in repo
        target_path = os.path.join(target_folder_path, unique_image_name)
        os.rename(image_path, target_path)

        # Git operations
        repo.index.add([os.path.join(TARGET_FOLDER, unique_image_name)])
        repo.index.commit(f"Added new image: {unique_image_name}")

        # Checkout the branch
        if BRANCH_NAME in repo.heads:
            repo.heads[BRANCH_NAME].checkout()
        else:
            repo.create_head(BRANCH_NAME)
            repo.heads[BRANCH_NAME].checkout()

        origin = repo.remote(name='origin')
        origin.push(refspec=f"{BRANCH_NAME}:{BRANCH_NAME}")

        # Construct raw GitHub file URL
        github_file_url = f"https://raw.githubusercontent.com/whiteandbox/codebase/refs/heads/{BRANCH_NAME}/{TARGET_FOLDER}/{unique_image_name}"
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

    # Commit and push the image to GitHub
    response = commit_and_push_image(temp_image_path)

    # Display the response
    if response["status"] == "success":
        st.success(f"File uploaded successfully: [View Image]({response['url']})")
    else:
        st.error(f"Error: {response['message']}")