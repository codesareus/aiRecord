import streamlit as st
from gtts import gTTS
from datetime import datetime

# Function to save text to a file
def save_text_to_file(text, filename="aiRecord.txt"):
    paragraphs = text.split("\n")
    with open(filename, "a") as file:
        for paragraph in paragraphs:
            if paragraph.strip():  # Check if the paragraph is not empty
                timestamp = datetime.now().strftime("%Y:%m:%d")
                paragraph_with_timestamp = f"{paragraph} [{timestamp}]"
                file.write("\n\n" + paragraph_with_timestamp)
    # Update the session state with the new content
    with open(filename, "r") as file:
        st.session_state.file_content = file.read()

# Function to search for keywords in the file content
def search_keywords_in_file(keywords, file_content):
    matching_paragraphs = []
    paragraphs = file_content.split("\n\n")  # Split text into paragraphs
    for paragraph in paragraphs:
        if all(keyword.lower() in paragraph.lower() for keyword in keywords):
            matching_paragraphs.append(paragraph.strip())
    return matching_paragraphs

# Function to extract timestamp from a paragraph
def extract_timestamp(paragraph):
    # Extract the timestamp from the end of the paragraph
    if "[" in paragraph and "]" in paragraph:
        timestamp_str = paragraph[paragraph.rfind("[") + 1 : paragraph.rfind("]")]
        try:
            return datetime.strptime(timestamp_str, "%Y:%m:%d")
        except ValueError:
            return None
    return None

# Function to add today's timestamp to paragraphs without one
def add_timestamp_to_paragraphs(paragraphs):
    updated_paragraphs = []
    for paragraph in paragraphs:
        if extract_timestamp(paragraph) is None:  # If no timestamp exists
            timestamp = datetime.now().strftime("%Y:%m:%d")
            updated_paragraph = f"{paragraph} [{timestamp}]"
            updated_paragraphs.append(updated_paragraph)
        else:
            updated_paragraphs.append(paragraph)
    return updated_paragraphs

# Function to sort paragraphs by timestamp and then by length
def sort_paragraphs(paragraphs):
    # Add timestamps to paragraphs without one
    paragraphs = add_timestamp_to_paragraphs(paragraphs)
    # Sort first by timestamp, then by length
    return sorted(paragraphs, key=lambda x: (extract_timestamp(x) or datetime.min, len(x)))

### function to clear text
def clear_text():
    st.session_state["text_area"] = ""

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

    # Input box for user to enter text
    user_text = st.text_area(
        "Enter your text (max 2000 characters):",
        value=st.session_state.text_area_content,
        max_chars=2000,
        key="text_area"
    )

    # Secret key input box (moved below the text window)
    secret_key = st.text_input("Enter the secret key to enable saving:", type="password")

    # Save button (disabled if secret key is incorrect)
    if secret_key == "zzzzzzzzz":
        save_button_disabled = False
    else:
        save_button_disabled = True

    # Use columns to place the Save Text button and confirmation message side by side
    col1, col2 = st.columns([1, 3])

    with col1:
        if st.button("Save Text", disabled=save_button_disabled):
            if user_text.strip():
                save_text_to_file(user_text)
                st.session_state.show_confirmation = True
                st.button("clear text input", on_click=clear_text)
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

    # Add a subtitle for the search functionality
    st.subheader("Search for Information")

    # Smaller text box for user to enter keywords
    search_phrase = st.text_input("Enter keywords to search (separated by spaces):")

    # Button to execute the search
    if st.button("Search"):
        if search_phrase:
            keyword_list = search_phrase.strip().split()
            matching_paragraphs = search_keywords_in_file(keyword_list, st.session_state.file_content)
            # Sort the matching paragraphs by timestamp and then by length
            st.session_state.matching_paragraphs = sort_paragraphs(matching_paragraphs)
        else:
            st.warning("Please enter keywords to search.")

    # Display matching paragraphs sorted by timestamp and length
    if st.session_state.matching_paragraphs:
        st.subheader("Matching Paragraphs (Sorted by Timestamp and Length):")
        for paragraph in st.session_state.matching_paragraphs:
            st.write(paragraph)
            st.write("")  # Add an empty line between paragraphs


if __name__ == "__main__":
    main()
