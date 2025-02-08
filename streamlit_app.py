import streamlit as st
from gtts import gTTS
from datetime import datetime, timedelta
import pytz
import re  # Import regex

midwest = pytz.timezone("America/Chicago")

# Function to save text to a file
def save_text_to_file(text, filename="aiRecord.txt"):
    if text.strip():  # Check if the text is not empty
        timestamp = datetime.now(midwest).strftime("%Y:%m:%d")
        text_with_timestamp = f"{{{text}}} [{timestamp}]"
        with open(filename, "a") as file:
            file.write("\n\n" + text_with_timestamp)

    # Update session state with new content
    with open(filename, "r") as file:
        st.session_state.file_content = file.read()

# Function to search for keywords in the file content
def search_keywords_in_file(keywords, file_content):
    matching_paragraphs = []
    paragraphs = re.findall(r'\{(.*?)\}', file_content, re.DOTALL)

    for paragraph in paragraphs:
        content_lower = " ".join(paragraph.lower().split())
        if all(kw.lower() in content_lower for kw in keywords):
            matching_paragraphs.append(paragraph.strip())

    return matching_paragraphs

# Function to extract timestamp from a paragraph
def extract_timestamp(paragraph):
    if "[" in paragraph and "]" in paragraph:
        timestamp_str = paragraph[paragraph.rfind("[") + 1 : paragraph.rfind("]")]
        try:
            return datetime.strptime(timestamp_str.strip(), "%Y:%m:%d")
        except ValueError:
            return None
    return None

# Function to sort paragraphs by timestamp and length
def sort_paragraphs(paragraphs):
    sorted_paragraphs = []
    for paragraph in paragraphs:
        timestamp = extract_timestamp(paragraph) or datetime.min
        sorted_paragraphs.append((timestamp, paragraph))
    sorted_paragraphs.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    return [p for _, p in sorted_paragraphs]

# Function to clear text input
def clear_text():
    st.session_state["text_area"] = ""

# Function to load keyword list from a file
def load_keyword_list(filename="keywords.txt"):
    try:
        with open(filename, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to get paragraphs by date
def get_paragraphs_by_date(file_content, target_date):
    paragraphs = file_content.split("\n\n")
    matching_paragraphs = []
    for paragraph in paragraphs:
        timestamp = extract_timestamp(paragraph)
        if timestamp and timestamp.date() == target_date.date():
            matching_paragraphs.append(paragraph)
    return matching_paragraphs

# Streamlit app
def main():
    st.title("AI Record App")

    # Initialize session state for file content
    if "file_content" not in st.session_state:
        try:
            with open("aiRecord.txt", "r") as file:
                st.session_state.file_content = file.read()
        except FileNotFoundError:
            st.session_state.file_content = ""

    # Initialize other session states
    if "text_area_content" not in st.session_state:
        st.session_state.text_area_content = ""
    if "matching_paragraphs" not in st.session_state:
        st.session_state.matching_paragraphs = []
    if "keyword_list" not in st.session_state:
        st.session_state.keyword_list = load_keyword_list()

    # Sidebar for keyword management
    with st.sidebar:
        st.subheader("Keyword List")
        keyword_input = st.text_area(
            "Enter keywords (one per line):",
            value="\n".join(st.session_state.keyword_list),
            height=150
        )

        if st.button("Save Keywords"):
            keywords = [k.strip() for k in keyword_input.splitlines() if k.strip()]
            with open("keywords.txt", "w") as file:
                file.write("\n".join(keywords))
            st.session_state.keyword_list = keywords
            st.success("Keywords saved successfully!")

        st.subheader("Saved Keywords")
        for keyword in st.session_state.keyword_list:
            if st.button(keyword):
                st.session_state.matching_paragraphs = search_keywords_in_file([keyword], st.session_state.file_content)
                st.session_state.matching_paragraphs = sort_paragraphs(st.session_state.matching_paragraphs)
                st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

    # Text input area
    user_text = st.text_area(
        "Enter your text (max 2000 characters):",
        value=st.session_state.text_area_content,
        max_chars=2000,
        key="text_area"
    )

    # Secret key input
    secret_key = st.text_input("Enter the secret key to enable saving:", type="password")
    save_button_disabled = secret_key != "zzzzzzzzz"

    # Save text button
    if st.button("Save Text", disabled=save_button_disabled):
        if user_text.strip():
            save_text_to_file(user_text)
            st.session_state.show_confirmation = True
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        else:
            st.warning("Text Box Empty!")

    if st.session_state.get("show_confirmation", False):
        st.success("Text saved successfully!")
        st.session_state.show_confirmation = False

    # Download button
    if st.button("Download Saved File"):
        if st.session_state.file_content:
            st.download_button(
                label="Download aiRecord.txt",
                data=st.session_state.file_content,
                file_name="aiRecord.txt",
                mime="text/plain"
            )
        else:
            st.error("No file found to download.")

    # Clear text button
    st.button("Clear Text Input", on_click=clear_text)

    # Search functionality
    st.subheader("Search for Information")
    search_phrase = st.text_input("Enter keywords to search (separated by spaces):")

    if st.button("Search"):
        if search_phrase:
            keyword_list = search_phrase.strip().split()
            st.session_state.matching_paragraphs = search_keywords_in_file(keyword_list, st.session_state.file_content)
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        else:
            st.warning("Please enter keywords to search.")

    # ytDay and toDay buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ytDay"):
            if st.session_state.file_content:
                yesterday = datetime.now(midwest) - timedelta(days=1)
                st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, yesterday)
                st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
            else:
                st.warning("No file content available.")

    with col2:
        if st.button("toDay"):
            if st.session_state.file_content:
                today = datetime.now(midwest)
                st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, today)
                st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
            else:
                st.warning("No file content available.")

    # Display matching paragraphs
    if st.session_state.matching_paragraphs:
        st.subheader("Matching Paragraphs:")
        editable_paragraphs = "\n\n".join(st.session_state.matching_paragraphs)
        edited_paragraphs = st.text_area("Edit Matching Paragraphs:", value=editable_paragraphs, height=300)

        # Copy button
        if st.button("Copy"):
            st.write("Copied to clipboard!")
            st.code(edited_paragraphs)
    else:
        st.warning("No matching paragraphs found.")

if __name__ == "__main__":
    main()
