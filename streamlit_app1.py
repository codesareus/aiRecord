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
        # Wrap the entire text in { ... } and append the timestamp
        text_with_timestamp = f"{{{text}}} [{timestamp}]"
        with open(filename, "a") as file:
            file.write("\n\n" + text_with_timestamp)
    # Update the session state with the new content
    with open(filename, "r") as file:
        st.session_state.file_content = file.read()

# Function to search for keywords in the file content
def search_keywords_in_file(keywords, file_content):
    matching_paragraphs = []

    # Use regex to extract all text inside curly braces
    paragraphs = re.findall(r'\{(.*?)\}', file_content, re.DOTALL)

    for paragraph in paragraphs:
        content = paragraph.strip()  # Trim spaces/newlines

        # Normalize spaces for comparison
        content_lower = " ".join(content.lower().split())
        keyword_checks = {kw.lower(): kw.lower() in content_lower for kw in keywords}

        # Check if all keywords are in the content
        if all(keyword_checks.values()):
            matching_paragraphs.append(content)

    return matching_paragraphs

# Function to extract timestamp from a paragraph
def extract_timestamp(paragraph):
    if "[" in paragraph and "]" in paragraph:
        timestamp_str = paragraph[paragraph.rfind("[") + 1 : paragraph.rfind("]")]
        try:
            return datetime.strptime(timestamp_str, "%Y:%m:%d")
        except ValueError:
            return None
    return None

# Function to sort paragraphs by timestamp and then by length
def sort_paragraphs(paragraphs):
    updated_paragraphs = []
    for paragraph in paragraphs:
        if paragraph.startswith("{") and paragraph.endswith("}"):
            timestamp_str = paragraph[paragraph.rfind("[") + 1 : paragraph.rfind("]")]
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y:%m:%d")
                updated_paragraphs.append((timestamp, paragraph))
            except ValueError:
                updated_paragraphs.append((datetime.min, paragraph))
    # Sort by timestamp and then by length
    updated_paragraphs.sort(key=lambda x: (x[0], len(x[1])), reverse=True)
    return [paragraph for _, paragraph in updated_paragraphs]

# Function to clear text
def clear_text():
    st.session_state["text_area"] = ""

# Function to remove duplicate paragraphs
def remove_duplicate_paragraphs(filename="aiRecord.txt"):
    with open(filename, "r") as file:
        paragraphs = file.read().split("\n\n")
    unique_paragraphs = list(set(paragraphs))
    with open(filename, "w") as file:
        file.write("\n\n".join(unique_paragraphs))

# Function to save keyword list to a file (overwrite mode)
def save_keyword_list(keywords, filename="keywords.txt"):
    with open(filename, "w") as file:
        file.write("\n".join(keywords))

# Function to load keyword list from a file
def load_keyword_list(filename="keywords.txt"):
    try:
        with open(filename, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to get paragraphs with a specific date's timestamp
def get_paragraphs_by_date(file_content, target_date):
    paragraphs = file_content.split("\n\n")
    matching_paragraphs = []
    for paragraph in paragraphs:
        if paragraph.startswith("{") and paragraph.endswith("}"):
            timestamp_str = paragraph[paragraph.rfind("[") + 1 : paragraph.rfind("]")]
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y:%m:%d")
                if timestamp.date() == target_date.date():
                    matching_paragraphs.append(paragraph)
            except ValueError:
                continue
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

    # Initialize session state for text area content
    if "text_area_content" not in st.session_state:
        st.session_state.text_area_content = ""

    # Initialize session state for search results and audio file
    if "matching_paragraphs" not in st.session_state:
        st.session_state.matching_paragraphs = []
    if "audio_file" not in st.session_state:
        st.session_state.audio_file = None

    # Load keyword list at app restart
    if "keyword_list" not in st.session_state:
        st.session_state.keyword_list = load_keyword_list()

    # Left side panel for keyword list input
    with st.sidebar:
        st.subheader("Keyword List")
        keyword_input = st.text_area(
            "Enter keywords (one per line):",
            value="\n".join(st.session_state.keyword_list),
            height=150
        )

        if st.button("Save Keywords"):
            if keyword_input.strip():
                keywords = [k.strip() for k in keyword_input.splitlines() if k.strip()]
                save_keyword_list(keywords)
                st.success("Keywords saved successfully!")
                st.session_state.keyword_list = keywords
            else:
                st.warning("No keywords entered!")

        st.subheader("Saved Keywords")
        for keyword in st.session_state.keyword_list:
            if st.button(keyword):
                st.session_state.matching_paragraphs = search_keywords_in_file([keyword], st.session_state.file_content)
                st.session_state.matching_paragraphs = sort_paragraphs(st.session_state.matching_paragraphs)

    # Input box for user to enter text
    user_text = st.text_area(
        "Enter your text (max 2000 characters):",
        value=st.session_state.text_area_content,
        max_chars=2000,
        key="text_area"
    )

    # Secret key input box
    secret_key = st.text_input("Enter the secret key to enable saving:", type="password")

    # Save button (disabled if secret key is incorrect)
    save_button_disabled = secret_key != "zzzzzzzzz"

    # Use columns to place the Save Text button and confirmation message side by side
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("Save Text", disabled=save_button_disabled):
            if user_text.strip():
                save_text_to_file(user_text)
                st.session_state.show_confirmation = True
            elif not user_text:
                st.warning("Text Box Empty!")
            else:
                st.warning("Only spaces present!")

    with col2:
        if st.session_state.get("show_confirmation", False):
            st.success("Text saved successfully!")
            st.session_state.show_confirmation = False
    
    # Download button for the saved file
    if st.button("Download Saved File"):
        if st.session_state.file_content:
            st.download_button(
                label="Download aiRecord.txt",
                data=st.session_state.file_content,
                file_name="aiRecord.txt",
                mime="text/plain"
            )
        else:
            st.error("No file found to download. Please save some text first.")

    # Clear text button
    st.button("Clear Text Input", on_click=clear_text)

    # Add a subtitle for the search functionality
    st.subheader("Search for Information")

    # Smaller text box for user to enter keywords
    search_phrase = st.text_input("Enter keywords to search (separated by spaces):")

    # Button to execute the search
    if st.button("Search"):
        if search_phrase:
            keyword_list = search_phrase.strip().split()
            matching_paragraphs = search_keywords_in_file(keyword_list, st.session_state.file_content)
            st.session_state.matching_paragraphs = matching_paragraphs  # Store results in session state
        else:
            st.warning("Please enter keywords to search.")

    # Buttons for ytDay, toDay, and Copy
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ytDay"):
            yesterday = datetime.now(midwest) - timedelta(days=1)
            st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, yesterday)
    with col2:
        if st.button("toDay"):
            today = datetime.now(midwest)
            st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, today)

    # Display matching paragraphs in an editable text area
    if st.session_state.matching_paragraphs:
        st.subheader("Matching Paragraphs:")
        # Join the matching paragraphs with double newlines for display
        editable_paragraphs = "\n\n".join(st.session_state.matching_paragraphs)
        # Display the matching paragraphs in an editable text area
        edited_paragraphs = st.text_area(
            "Edit Matching Paragraphs:",
            value=editable_paragraphs,
            height=300
        )

        # Add a button to copy the edited paragraphs to the clipboard
        if st.button("Copy"):
            st.write("Copied to clipboard!")
            st.code(edited_paragraphs)
    else:
        st.warning("No matching paragraphs found.")

if __name__ == "__main__":
    main()
