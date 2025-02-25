import streamlit as st
from gtts import gTTS
from datetime import datetime, timedelta
import pytz
import re  # Import regex
import os

midwest = pytz.timezone("America/Chicago")
# Define the filename in the same directory as the script
FILE_NAME = "aiRecord.txt"
FILE_PATH = os.path.join(os.path.dirname(__file__), FILE_NAME)

# Function to save text to a file
def save_text_to_file(text, filename="aiRecord.txt"):
    if text.strip():  # Check if the text is not empty
        timestamp = datetime.now(midwest).strftime("%Y:%m:%d")
        timestp = datetime.now(midwest).strftime("%Y-%m-%d: ")
        text_with_timestamp = "{" + timestp + f" {text}" + "}" +  f"[{timestamp}]"
        with open(filename, "a") as file:
            file.write("\n\n" + text_with_timestamp)

    # Update session state with new content
    with open(filename, "r") as file:
        st.session_state.file_content = file.read()

# Function to search for keywords in the file content
def search_keywords_in_file(keywords, file_content):
    matching_paragraphs = []
    matches = re.findall(r'(\{.*?\})\s*(\[\d{4}:\d{2}:\d{2}\])', file_content, re.DOTALL)
    
    for content, timestamp in matches:
        content_lower = " ".join(content.lower().split())
        if all(kw.lower() in content_lower for kw in keywords):
            highlighted_content = content  # Copy content for modification
            
            # Change highlight color
            highlight_color = "#efd06c"  # Change this to match your theme

            for kw in keywords:
                highlighted_content = re.sub(
                    rf"({re.escape(kw)})",
                    rf'<span style="background-color: {highlight_color}; color: black; font-weight: bold; padding: 2px 4px; border-radius: 3px;">\1</span>',
                    highlighted_content,
                    flags=re.IGNORECASE
                )

            matching_paragraphs.append(f"{highlighted_content} {timestamp}")

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
    st.session_state.text_saved = False  # Re-enable "Save Text"
    st.session_state.show_confirmation = False
    st.session_state.new_text_saved = False

# Function to load keyword list from a file
def load_keyword_list(filename="keywords.txt"):
    try:
        with open(filename, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []


# Function to get paragraphs by date with trimmed content
def get_paragraphs_by_date(file_content, target_date):
    paragraphs = file_content.split("{")
    matching_paragraphs = []
    for paragraph in paragraphs:
        timestamp = extract_timestamp(paragraph)
        if timestamp and timestamp.date() == target_date.date():
            #trimmed_text = paragraph[-30:]  # Get only the last 20 characters
            #trimmed_text1 = paragraph[:20]  # Get only the first 20 characters
            matching_paragraphs.append(paragraph)
    return matching_paragraphs

# Function to generate and play speech
# Function to clean text (removes numbers and special characters

def clean_textsymbols(text, lang="zh"):
    """
    Cleans the text by removing unwanted symbols and characters based on the specified language mode.
    
    Args:
        text (str): The input text to be cleaned.
        language_mode (str): The language mode. Can be "English" or "Chinese".
                             - If "English", all Chinese characters are removed.
                             - If "Chinese", all English characters are removed.
                             
    Returns:
        str: The cleaned text.
    """
    if lang == "en":
        # Keep English letters, spaces, commas, and periods; remove everything else
        #text = re.sub(r'[^\u0020-\u007E\u4e00-\u9fff]', '', text)  # Remove non-ASCII and non-Chinese characters
        #text = re.sub(r'[\u4e00-\u9fff]', '', text)  # Remove Chinese characters
        text = re.sub(r'[^A-Za-z\s,.]', '', text)  # Keep only English letters, spaces, commas, and periods
    elif lang == "zh":
        # Keep Chinese characters, spaces, commas, and periods; remove everything else
        text = re.sub(r'[^\u4e00-\u9fff\s，。]', '', text)  # Keep only Chinese characters, spaces, and Chinese punctuation
        #text = re.sub(r'[^\u0020-\u007E\u4e00-\u9fff]', '', text)  # Remove non-ASCII and non-Chinese characters
        #text = re.sub(r'[A-Za-z]', '', text)  # Remove English letters   
    else:
        raise ValueError("Invalid language_mode. Use 'English' or 'Chinese'.")
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra spaces
    return text
    
# Function to generate speech
def text_to_speech(text, lang="en", filename="speech.mp3"):
    cleaned_text = clean_textsymbols(text)  # Clean the text before conversion
    tts = gTTS(cleaned_text, lang=lang)
    tts.save(filename)
    return filename

#def text_to_speech(text, lang="en", filename="speech.mp3"):
   # tts = gTTS(text, lang=lang)
 #   tts.save(filename)
  #  return filename

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
    if "search_phrase" not in st.session_state:
        st.session_state.search_phrase = ""

# Initialize session state variables
    
    if "show_confirmation" not in st.session_state:
        st.session_state.show_confirmation = False
    if "show_deletion_confirmation" not in st.session_state:
        st.session_state.show_deletion_confirmation = False
    if "new_text_saved" not in st.session_state:
        st.session_state.new_text_saved = False  # Track if new text has been saved
    if "text_saved" not in st.session_state:
        st.session_state.text_saved = False  # Track if text has been saved



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
##########################
        #st.subheader("Saved Keywords")

# Assuming keyword_list is stored in session state
        if 'keyword_list' not in st.session_state:
            st.session_state.keyword_list = []

# Display subheader
        st.subheader("Saved Keywords")

# Define the number of columns you want per row
        columns_per_row = 4  # You can adjust this based on your preference

# Calculate the number of rows needed
        num_keywords = len(st.session_state.keyword_list)
        num_rows = -(-num_keywords // columns_per_row)  # Ceiling division to determine rows

# Loop through the keywords and display them in a grid
        for row in range(num_rows):
    # Create columns for each row
            cols = st.columns(columns_per_row)
    
    # Iterate over the columns and place buttons inside
            for col_idx in range(columns_per_row):
                keyword_index = row * columns_per_row + col_idx
        
        # Check if there are still keywords left to display
                if keyword_index < num_keywords:
                    keyword = st.session_state.keyword_list[keyword_index]
            
            # Place the button inside the column
                    with cols[col_idx]:
                        if st.button(keyword):
                            st.session_state.search_phrase = keyword
                            st.session_state.matching_paragraphs = search_keywords_in_file([keyword], st.session_state.file_content)
                            st.session_state.matching_paragraphs = sort_paragraphs(st.session_state.matching_paragraphs)
                            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        
       # for keyword in st.session_state.keyword_list:
            #if st.button(keyword):
                #st.session_state.search_phrase = keyword
               # st.session_state.matching_paragraphs = search_keywords_in_file([keyword], st.session_state.file_content)
               # st.session_state.matching_paragraphs = sort_paragraphs(st.session_state.matching_paragraphs)
              #  st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

    # Text input area
    user_text = st.text_area(
        "Enter your text (max 5000 characters):",
        value=st.session_state.text_area_content,
        max_chars=5000,
        key="text_area",
        height=300
    )

    # Secret key input
    secret_key = st.text_input("Enter the secret key to enable saving:", type="password")
    save_button_disabled = secret_key != "zzzzzzzzz" or st.session_state.text_saved

    # Save text button
    if st.button("Save Text", disabled=save_button_disabled):
        if user_text.strip():
            save_text_to_file(user_text)
            st.session_state.show_confirmation = True
            st.session_state.new_text_saved = True  # Enable "Delete Last" after saving
            st.session_state.text_saved = True  # Disable "Save Text" after saving
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        else:
            st.warning("Text Box Empty!")
                
    # Show confirmation message and ClearInput button
    if st.session_state.get("show_confirmation", False):
        st.success("Text saved successfully!")
        st.button("ClearInput", on_click=clear_text)
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


#################

    # Search functionality
    st.subheader("Search for Information")
    search_phrase = st.text_input(
        "Enter keywords to search (separated by spaces):",
        value=st.session_state.search_phrase
    )

    if st.button("Search"):
        if search_phrase:
            keyword_list = search_phrase.strip().split()
            st.session_state.matching_paragraphs = search_keywords_in_file(keyword_list, st.session_state.file_content)
            st.session_state.matching_paragraphs = sort_paragraphs(st.session_state.matching_paragraphs)
            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
        else:
            st.warning("Please enter keywords to search.")

    # Initialize session state for expand/collapse
    if "expand_all" not in st.session_state:
        st.session_state.expand_all = False  # Default: collapsed

    # ytDay and toDay buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("-2days"):
            if st.session_state.get("file_content"):
                dbytd = datetime.now(midwest) - timedelta(days=2)
                st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, dbytd)
                st.rerun()
            #else:
                #st.warning("No file content available.")

            if st.button("-3days"):
                if st.session_state.get("file_content"):
                    dbytd = datetime.now(midwest) - timedelta(days=3)
                    st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, dbytd)
                    st.rerun()
                else:
                    st.warning("No file content available.")
                       
    with col2:
        if st.button("ytDay"):
            if st.session_state.get("file_content"):
                yesterday = datetime.now(midwest) - timedelta(days=1)
                st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, yesterday)
                st.rerun()
            else:
                st.warning("No file content available.")

    with col3:
        if st.button("toDay"):
            if st.session_state.get("file_content"):
                today = datetime.now(midwest)
                st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, today)
                st.rerun()
            else:
                st.warning("No file content available.")

    # Button to toggle expand/collapse state
    with col4:
        if st.button("Expand All" if not st.session_state.expand_all else "Collapse All"):
            st.session_state.expand_all = not st.session_state.expand_all
            st.rerun()

    # Display matching paragraphs
    if st.session_state.get("matching_paragraphs"):
        st.subheader(f"Matching Paragraphs:({search_phrase})")

        if st.session_state.expand_all:
        # Show all paragraphs as a single block for easy copying (preserving highlights)
            full_text = "<br><br>".join(st.session_state.matching_paragraphs)
            st.markdown(full_text, unsafe_allow_html=True)
            
            if st.button("🔊 听 (中文)"):
                speech_file = text_to_speech(full_text, lang="zh")
                st.audio(speech_file)

            # Add download button
                with open(speech_file, "rb") as f:
                    audio_bytes = f.read()
    
                    st.download_button(
                        label="⬇️ 下载语音文件",
                        data=audio_bytes,
                           # file_name=f"speech_{idx}.mp3",
                        file_name=f"{search_phrase}_全部.mp3",
                        mime="audio/mpeg",
                        key=f"download_全部"
                    )
        # Copy button (removes HTML tags before copying)
            if st.button("Copy"):
                plain_text = re.sub(r'<.*?>', '', full_text)  # Remove HTML tags
                st.code(plain_text)
                st.write("Copied to clipboard!")

        else:
        # Show each paragraph as an expandable block without highlights when collapsed
            for idx, paragraph in enumerate(st.session_state.matching_paragraphs):
                truncated_text = f"......{paragraph[:50]}"  # Show only the first 50 characters

                with st.expander(truncated_text):
                # Ensure highlights work when expanded
                    cleaned_paragraph = f'<div style="white-space: pre-wrap;">{paragraph}</div>'
                    st.markdown(cleaned_paragraph, unsafe_allow_html=True)

                # Speech buttons for individual paragraphs

                    if st.button(f"🔊 听 (中文) {idx}", key=f"listen_zh_{idx}"):
                        speech_file = text_to_speech(paragraph, lang="zh", filename=f"speech_{idx}.mp3")
                        st.audio(speech_file)
                        # Add download button
                        with open(speech_file, "rb") as f:
                            audio_bytes = f.read()
    
                        st.download_button(
                            label="⬇️ 下载语音文件",
                            data=audio_bytes,
                           # file_name=f"speech_{idx}.mp3",
                            file_name=f"{search_phrase}_{idx}.mp3",
                            mime="audio/mpeg",
                            key=f"download_{idx}"
                        )
    else:
        st.warning("No matching paragraphs found.")

if __name__ == "__main__":
    main()
