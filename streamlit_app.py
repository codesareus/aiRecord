import streamlit as st
from gtts import gTTS

# Function to save text to a file
def save_text_to_file(text, filename="aiRecord.txt"):
    with open(filename, "a") as file:
        file.write("\n\n" + text)  # Add an extra newline to separate paragraphs
    # Update the session state with the new content
    with open(filename, "r") as file:
        st.session_state.file_content = file.read()

# Function to search for keywords in the file content
def search_keywords_in_file(keywords, file_content):
    matching_paragraphs = []
    paragraphs = file_content.split("\n\n")  # Split text into paragraphs
    for paragraph in paragraphs:
        # Check if all keywords are present in the paragraph (case-insensitive)
        if all(keyword.lower() in paragraph.lower() for keyword in keywords):
            matching_paragraphs.append(paragraph.strip())  # Strip whitespace and add to list
    # Remove duplicate paragraphs
    unique_paragraphs = list(set(matching_paragraphs))
    # Sort paragraphs by length (shortest first)
    unique_paragraphs.sort(key=len)
    return unique_paragraphs

### function to clear text
def clear_text():
    st.session_state["text_area"] = ""

# Function to detect language
def detect_language(text):
    try:
        lang = detect(text)
        if lang == "zh-cn" or lang == "zh-tw":
            return "zh"  # Chinese
        else:
            return "en"  # Default to English
    except:
        return "en"  # Fallback to English if detection fails

# Streamlit app
def main():
    st.title("AI Record App")

    # Initialize session state for file content
    if "file_content" not in st.session_state:
        try:
            with open("aiRecord.txt", "r") as file:
                st.session_state.file_content = file.read()
        except FileNotFoundError:
            st.session_state.file_content = ""  # Initialize with empty content if file doesn't exist

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
    col1, col2 = st.columns([1, 3])  # Adjust the ratio as needed

    with col1:
        if st.button("Save Text", disabled=save_button_disabled):
            if user_text.strip():  # Check if the text is not empty or only spaces
                save_text_to_file(user_text)
                st.session_state.show_confirmation = True  # Show confirmation message
                st.button("clear text input", on_click=clear_text)
            elif not user_text:  # Check if the text is empty
                st.warning("Text Box Empty!")
            else:  # If the text contains only spaces
                st.warning("Only spaces present!")

    with col2:
        if st.session_state.get("show_confirmation", False):
            st.success("Text saved successfully!")
            st.session_state.show_confirmation = False  # Reset the confirmation message

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
            # Split the search phrase into individual words
            keyword_list = search_phrase.strip().split()
            st.session_state.matching_paragraphs = search_keywords_in_file(keyword_list, st.session_state.file_content)
        else:
            st.warning("Please enter keywords to search.")

    # Display matching paragraphs
    if st.session_state.matching_paragraphs:
        st.subheader("Matching Paragraphs:")
        for paragraph in st.session_state.matching_paragraphs:
            st.write(paragraph)
            st.write("")  # Add an empty line between paragraphs


if __name__ == "__main__":
    main()
