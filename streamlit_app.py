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
    
        # Save Keywords button
        if st.button("Save Keywords"):
            keywords = [k.strip() for k in keyword_input.splitlines() if k.strip()]
            with open("keywords.txt", "w") as file:
                file.write("\n".join(keywords))
            st.session_state.keyword_list = keywords
            st.success("Keywords saved successfully!")
    
        st.subheader("Saved Keywords")

    with st.sidebar:
    # Arrange saved keywords in columns
        if st.session_state.keyword_list:
            num_columns = 3  # Number of columns to display buttons in
            keyword_chunks = [st.session_state.keyword_list[i:i + num_columns] for i in range(0, len(st.session_state.keyword_list), num_columns)]
    
            for chunk in keyword_chunks:
                cols = st.columns(num_columns)
                for i, keyword in enumerate(chunk):
                    with cols[i]:
                        if st.button(keyword, key=f"keyword_{keyword}"):
                            st.session_state.search_phrase = keyword
                            st.session_state.matching_paragraphs = search_keywords_in_file([keyword], st.session_state.file_content)
                            st.session_state.matching_paragraphs = sort_paragraphs(st.session_state.matching_paragraphs)
                            st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

    ## upload
    
    show_upload = st.checkbox("Upload local records", value=False)
    
    if show_upload:
        uploaded_file = st.file_uploader("Choose txt file", type=["txt"])
        
        if uploaded_file is not None:
            st.session_state.file_content = uploaded_file.read().decode('utf-8')
            
    # Text input area
    user_text = st.text_area(
        "Enter your text (max 2000 characters):",
        value=st.session_state.text_area_content,
        max_chars=2000,
        key="text_area",
        height=300
    )

    recentR= st.checkbox("show recent records")
    if recentR:
        st.code(f"Recent: {st.session_state.file_content[-1900:]}")
    else:
        content_without_whitespace = "".join(st.session_state.file_content[-20:-1].split())# space is cause line breaks in display
        st.code(f"Last: {content_without_whitespace}...{st.session_state.file_content.split("\n\n")[0]}")

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
    col1, col2= st.columns(2)
    with col1:
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

    with col2:
        if st.checkbox("show all records"):
            if st.session_state.file_content:
                st.code(st.session_state.file_content)
                
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
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("ytDay"):
            if st.session_state.get("file_content"):
                yesterday = datetime.now(midwest) - timedelta(days=1)
                st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, yesterday)
                st.rerun()
            else:
                st.warning("No file content available.")

    with col2:
        if st.button("toDay"):
            if st.session_state.get("file_content"):
                today = datetime.now(midwest)
                st.session_state.matching_paragraphs = get_paragraphs_by_date(st.session_state.file_content, today)
                st.rerun()
            else:
                st.warning("No file content available.")

    # Button to toggle expand/collapse state
    with col3:
        if st.button("Expand All" if not st.session_state.expand_all else "Collapse All"):
            st.session_state.expand_all = not st.session_state.expand_all
            st.rerun()

    # Display matching paragraphs
    if st.session_state.get("matching_paragraphs"):
        st.subheader("Matching Paragraphs:")

        if st.session_state.expand_all:
            # Show all paragraphs as a single block for easy copying (preserving highlights)
            full_text = "<br><br>".join(st.session_state.matching_paragraphs)
            st.markdown(full_text, unsafe_allow_html=True)

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

    else:
        st.warning("No matching paragraphs found.")


if __name__ == "__main__":
    main()

#######
import streamlit as st
from textblob import TextBlob
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime
import pytz

CSV_FILE = "mood_history.csv"
MOOD_EMOJIS = {
    'Happy': '😊', 
    'Sad': '😢',
    'Energetic': '💪',
    'Calm': '🧘',
    'Creative': '🎨',
    'Stressed': '😰',
    'Neutral': '😐'
}

#st.set_page_config(page_title="Mood Diary", page_icon="📔")
st.title("📔 Daily Mood Diary")
st.write("Document your daily mood with two sentences!")

# Collapsible upload block
show_upload = st.checkbox("Upload custom mood history")
uploaded_file = None
if show_upload:
    uploaded_file = st.file_uploader("Upload your mood history CSV", type=["csv"])

# Initialize or load data
if uploaded_file is not None:
    st.session_state.mood_history = pd.read_csv(uploaded_file, parse_dates=["Date"])
else:
    if os.path.exists(CSV_FILE):
        st.session_state.mood_history = pd.read_csv(CSV_FILE, parse_dates=["Date"])
    else:
        st.session_state.mood_history = pd.DataFrame(columns=[
            "Date", "Sentence 1", "Sentence 2", 
            "Predicted Mood", "Mood Score", "Emoji"
        ])

st.write("## Daily Entry")

# Determine if today's entry exists
today_date = datetime.now().date()
submitted_today = False
if not st.session_state.mood_history.empty and 'Date' in st.session_state.mood_history:
    submitted_today = today_date in pd.to_datetime(st.session_state.mood_history["Date"]).dt.date.values

with st.form("daily_entry"):
    sentence1 = st.text_area("First sentence:", disabled=submitted_today,
                             placeholder="How are you feeling today?", height=68)
    sentence2 = st.text_area("Second sentence:", disabled=submitted_today,
                             placeholder="What's been on your mind?", height=68)
    submitted = st.form_submit_button("Save Today's Entry", disabled=submitted_today)

def analyze_mood(sentence1, sentence2):
    combined_text = f"{sentence1} {sentence2}"
    analysis = TextBlob(combined_text)
    polarity = analysis.sentiment.polarity
    
    if polarity > 0.3:
        mood = "Happy"
    elif polarity < -0.3:
        mood = "Sad"
    else:
        mood = "Neutral"
        
    return mood, polarity, MOOD_EMOJIS.get(mood, "")

if submitted and sentence1.strip() and sentence2.strip():
    mood, score, emoji = analyze_mood(sentence1, sentence2)
    today = datetime.now()
    
    new_entry = {
        "Date": today,
        "Sentence 1": sentence1,
        "Sentence 2": sentence2,
        "Predicted Mood": mood,
        "Mood Score": round(score, 2),
        "Emoji": emoji
    }
    
    new_entry_df = pd.DataFrame([new_entry])
    st.session_state.mood_history = pd.concat([st.session_state.mood_history, new_entry_df], ignore_index=True)
    
    # Save to server CSV only if no file was uploaded
    if not show_upload:
        new_entry_df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
    
    st.success("Entry saved successfully!")
    st.balloons()
    submitted_today = True  # Immediately reflect the submission

elif submitted:
    st.warning("Please fill in both sentences!")

if submitted_today:
    st.subheader("Today's Mood")
    col1, col2 = st.columns(3)
    today_entry = st.session_state.mood_history.iloc[-1]
    with col1:
        st.metric("Predicted Mood", f"{today_entry['Predicted Mood']} {today_entry['Emoji']}")
    with col2:
        st.metric("Mood Score", f"{today_entry['Mood Score']:.2f}")
        
csv = st.session_state.mood_history.to_csv(index=False).encode('utf-8')
st.download_button(
            label="Download History",
            data=csv,
            file_name="mood_history.csv",
            mime="text/csv"
        )     

if not st.session_state.mood_history.empty:
    st.subheader("Your Mood History")
    display_df = st.session_state.mood_history.tail(5).copy()
    display_df["Date"] = pd.to_datetime(display_df["Date"]).dt.strftime("%Y-%m-%d")
    st.dataframe(display_df.style.format({"Mood Score": "{:.2f}"}))

    st.subheader("Mood Timeline (Current Month)")
    current_month = datetime.now().month
    current_year = datetime.now().year

    monthly_data = st.session_state.mood_history[
        (pd.to_datetime(st.session_state.mood_history["Date"]).dt.month == current_month) &
        (pd.to_datetime(st.session_state.mood_history["Date"]).dt.year == current_year)]
    
    if not monthly_data.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(pd.to_datetime(monthly_data["Date"]), monthly_data["Mood Score"], 
                marker='o', linestyle='-', color='skyblue', label="Mood Score")
        
        for date, score, emoji in zip(pd.to_datetime(monthly_data["Date"]), monthly_data["Mood Score"], monthly_data["Emoji"]):
            ax.text(date, score + 0.001, emoji, fontsize=16, ha='center', va='bottom', color="orange")
        
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d'))
        plt.xticks(rotation=45)
        ax.set_xlabel("Day of Month")
        ax.set_ylabel("Mood Score")
        ax.set_title(f"Mood Timeline ({datetime.now().strftime('%B %Y')})")
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.info("No data available for the current month.")

st.markdown("---")
st.caption("Your personal mood diary - Reflect, remember, and grow.")

#########
import time
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import tempfile
import os

# Set up the Streamlit app title
st.title("Fireworks Animation")

# Define the shapes of letters and numbers with improved coordinates
def get_letter_shapes():
    # Coordinates for the characters (scaled and centered)
    H = np.array([
        [-0.8, -1], [-0.8, 1],  # Left vertical
        [0.8, -1], [0.8, 1],    # Right vertical
        [-0.8, 0], [0.8, 0]     # Horizontal bar
    ]) * 1.5

    Six = np.array([
        [1, 1],          # Top start
        [-1, 0.5],       # Left curve top
        [-1, -0.5],      # Left curve bottom
        [0, -1],         # Bottom center
        [1, -0.5],       # Right curve bottom
        [0.5, 0],        # Inner curve
        [0, 0.5]         # Closing point
    ]) * 1.5
    
    Zero = np.array([
        [0, 1], [-0.5, 0.87], [-0.87, 0.5], [-1, 0],  # Left semicircle
        [-0.87, -0.5], [-0.5, -0.87], [0, -1],        # Bottom semicircle
        [0.5, -0.87], [0.87, -0.5], [1, 0],           # Right semicircle
        [0.87, 0.5], [0.5, 0.87], [0, 1]              # Top semicircle
    ]) * 1.5

    # Points for "Y"
    Y = np.array([[-1, 1], [0, 0], [0, -1], [0.25, 0], [1, 1]]) * 2

    W = np.array([[-1, 0.75], [-0.5, -0.75], [0, 0], [0.5, -0.75], [1, 0.75]]) * 2

    # Define the shape for '1'
    One = np.array([
        [0, 1],    # Top of the '1'
        [0, -1],   # Bottom of the '1'
        [-0.3, 0.8],  # Small angled stroke at top left
        [0, 1],    # Connect back to top
        [0.3, 0.8],   # Small angled stroke at top right
        [0, 1],    # Back to top
        [-0.2, -1],  # Bottom left of base
        [0.2, -1]    # Bottom right of base
    ]) * 1.5

    # Corrected shape for 'K'
    K = np.array([
        [-1, 1], [-1, -1], [-1, 0],  # Upper diagonal arm
        [1, 1], [0, 0], [1, -1]   # Lower diagonal arm
    ]) * 1.5

    # Edges for each character (explicit connections between points)
    letter_edges = {
        'H': [(0, 1), (2, 3), (4, 5)],  # Connect left, right, and middle bars
        'A': [(0, 1), (1, 2), (2, 3), (4, 5)],  # Triangle and horizontal bar
        'P': [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)],  # Circular P
        'Y': [(0, 1), (1, 2), (2, 3), (2, 4)],  # Correct "Y" shape
        'W': [(0, 1), (1, 2), (2, 3), (3, 4)],  # Peaks of M
        'S': [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,0)],  # Continuous 6 shape
        'Z': [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (11,0)],  # Full circle
        '1': [(0, 1), (2, 3), (3, 4), (4, 5), (6, 7)],  # Vertical stroke, angled top, and base
        'K': [(0, 1), (2, 3), (4, 5)]  # Spine and two diagonal arms
    }

    return {
        'H': H, 
        'A': np.array([[-1, -1], [-0.5, 1], [0.5, 1], [1, -1], [-0.5, 0], [0.5, 0]]) * 2,
        'P': np.array([[-1, -1], [-1, 1], [0, 1], [1, 0], [-1, 0]]) * 2,
        'Y': Y,  # Updated "Y" points
        'W': W,
        'S': Six,
        'Z': Zero,
        '1': One,  # Add '1' to the returned dictionary
        'K': K     # Add 'K' to the returned dictionary
    }, letter_edges

# Modified firework generation with better particle control
def generate_firework(ax, x_center, y_center, is_word=False, character=None):
    letter_shapes, letter_edges = get_letter_shapes()
    if is_word and character:
        num_particles_per_point = 15  # Increased particle density
        letter_shape = letter_shapes[character]
        edges = letter_edges[character]
        x, y = [], []
        
        # Add intermediate points for better shape definition
        for edge in edges:
            start_idx, end_idx = edge
            start = letter_shape[start_idx]
            end = letter_shape[end_idx]
            points = np.linspace(start, end, 5)
            for point in points:
                offsets = np.random.normal(loc=point, scale=0.1, size=(num_particles_per_point, 2))
                x.extend(offsets[:, 0] + x_center)
                y.extend(offsets[:, 1] + y_center)
        
        scatter = ax.scatter(x, y, s=20, c=np.random.rand(3,), alpha=0.95, edgecolors="none")
    else:
        num_particles = 200
        num_center_particles = int(num_particles * 0.2)
        num_outer_particles = num_particles - num_center_particles
        center_x = np.random.normal(loc=x_center, scale=0.5, size=num_center_particles)
        center_y = np.random.normal(loc=y_center, scale=0.5, size=num_center_particles)
        angles = np.linspace(0, 2 * np.pi, num_outer_particles)
        radii = np.random.uniform(1, 4, size=num_outer_particles)
        outer_x = x_center + radii * np.cos(angles)
        outer_y = y_center + radii * np.sin(angles)
        x = np.concatenate([center_x, outer_x])
        y = np.concatenate([center_y, outer_y])
        scatter = ax.scatter(x, y, s=15, c=np.random.rand(3,), alpha=0.9, edgecolors="none")
    return scatter

# Function to update the fireworks animation
def update(frame, ascending_fireworks, exploded_scatters, ax, series_launched, runner_info):
    # Launch the 1000K series at frame 50
    if frame == 125 and not series_launched[0]:
        series_letters = ['1','Z','Z','Z','K']
        num_letters = len(series_letters)
        explosion_heights = np.linspace(20, 20 + num_letters*1.5, num_letters)
        series_x = np.linspace(-18, 18, num_letters)
        for i, char in enumerate(series_letters):
            scatter = ax.scatter(series_x[i], -5, s=10, c="white", alpha=0.8)
            ascending_fireworks.append({
                "scatter": scatter,
                "x": series_x[i],
                "y": -5,
                "speed": 1.5,
                "explosion_height": explosion_heights[i],
                "character": char
            })
        series_launched[0] = True

    # Update ascending fireworks
    for firework in ascending_fireworks.copy():
        firework["y"] += firework["speed"]
        firework["scatter"].set_offsets([firework["x"], firework["y"]])
        if firework["y"] >= firework["explosion_height"]:
            if "character" in firework:
                exploded_scatters.append(generate_firework(ax, firework["x"], firework["y"], is_word=True, character=firework["character"]))
            else:
                if np.random.rand() < 0.3:
                    exploded_scatters.append(generate_firework(ax, firework["x"], firework["y"], is_word=True))
                else:
                    exploded_scatters.append(generate_firework(ax, firework["x"], firework["y"]))
            firework["scatter"].remove()
            ascending_fireworks.remove(firework)

    # Update exploded fireworks particles
    for scatter in exploded_scatters.copy():
        offsets = scatter.get_offsets()
        offsets[:, 1] -= 0.2
        scatter.set_offsets(offsets)
        current_alpha = scatter.get_alpha()
        new_alpha = max(0.0, min(1.0, current_alpha - 0.02))
        scatter.set_alpha(new_alpha)
        if new_alpha <= 0:
            scatter.remove()
            exploded_scatters.remove(scatter)

    # Add new ascending fireworks occasionally
    if frame % 10 == 0 and not series_launched[0]:
        x_start = np.random.uniform(-10, 10)
        y_start = -5
        explosion_height = np.random.uniform(15, 40)
        speed = np.random.uniform(0.5, 1.0)
        scatter = ax.scatter(x_start, y_start, s=10, c="white", alpha=0.8)
        ascending_fireworks.append({
            "scatter": scatter,
            "x": x_start,
            "y": y_start,
            "speed": speed,
            "explosion_height": explosion_height
        })

    # Launch the runner after the 1000K series is completed
    if series_launched[0] and not runner_info['active'] and len(ascending_fireworks) == 0:
        runner_info['active'] = True
        runner_info['y_pos'] = -5
        runner_info['x_pos'] = 0
        runner_info['speed'] = 1.5
        runner_info['pose'] = 0
        runner_info['animation_counter'] = 0
        
        # Create runner's graphical elements (scaled 5x)
        runner_info['head'] = plt.Circle((runner_info['x_pos'], runner_info['y_pos']), 
                                    radius=1.5, 
                                    color=runner_info['color'],  # Use custom color
                                    zorder=10)
        ax.add_patch(runner_info['head'])
        
        # Initialize body parts with custom color
        runner_info['body'], = ax.plot([], [], color=runner_info['color'], lw=10, zorder=10)
        runner_info['left_arm'], = ax.plot([], [], color=runner_info['color'], lw=10, zorder=10)
        runner_info['right_arm'], = ax.plot([], [], color=runner_info['color'], lw=10, zorder=10)
        runner_info['left_leg'], = ax.plot([], [], color=runner_info['color'], lw=10, zorder=10)
        runner_info['right_leg'], = ax.plot([], [], color=runner_info['color'], lw=10, zorder=10)

    # Update runner's position and animation
    if runner_info['active']:
        runner_info['y_pos'] += runner_info['speed']
        runner_info['animation_counter'] += 1
        
        if runner_info['animation_counter'] >= 5:
            runner_info['pose'] = 1 - runner_info['pose']
            runner_info['animation_counter'] = 0

        x = runner_info['x_pos']
        y = runner_info['y_pos']
        
        # Update head position
        runner_info['head'].center = (x, y)
        
        # Update body position (scaled 5x)
        runner_info['body'].set_data([x, x], [y - 2.5, y - 7.5])
        
        # Update arms and legs based on pose
        if runner_info['pose'] == 0:
            runner_info['left_arm'].set_data([x - 2.5, x], [y - 2.5, y - 2.5])
            runner_info['right_arm'].set_data([x + 2.5, x], [y - 2.5, y + 2.5])
            runner_info['left_leg'].set_data([x - 2.5, x - 2.5], [y - 7.5, y - 12.5])
            runner_info['right_leg'].set_data([x + 2.5, x + 2.5], [y - 7.5, y - 5.0])
        else:
            runner_info['left_arm'].set_data([x - 2.5, x], [y - 2.5, y + 2.5])
            runner_info['right_arm'].set_data([x + 2.5, x], [y - 2.5, y - 2.5])
            runner_info['left_leg'].set_data([x - 2.5, x - 2.5], [y - 7.5, y - 5.0])
            runner_info['right_leg'].set_data([x + 2.5, x + 2.5], [y - 7.5, y - 12.5])

        # Hide runner when out of bounds
        if runner_info['y_pos'] > 40:
            runner_info['head'].center = (100, 100)  # Move off-screen
            runner_info['body'].set_data([], [])
            runner_info['left_arm'].set_data([], [])
            runner_info['right_arm'].set_data([], [])
            runner_info['left_leg'].set_data([], [])
            runner_info['right_leg'].set_data([], [])
            runner_info['active'] = False

def main():
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.set_xlim(-30, 30)
    ax.set_ylim(-10, 40)
    ax.axis("off")

    ascending_fireworks = []
    exploded_scatters = []
    series_launched = [False]  # Track if series has been launched
    runner_info = {
        'active': False,
        'y_pos': -5,
        'x_pos': 0,
        'speed': 1.5,
        'pose': 0,
        'animation_counter': 0,
        'color': 'cyan',  # Customizable runner color
        'head': None,
        'body': None,
        'left_arm': None,
        'right_arm': None,
        'left_leg': None,
        'right_leg': None
    }

    ani = FuncAnimation(fig, update, frames=200, fargs=(ascending_fireworks, exploded_scatters, ax, series_launched, runner_info), interval=50, blit=False)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as tmpfile:
        try:
            ani.save(tmpfile.name, writer="pillow", fps=20)
            gif_path = tmpfile.name
        except Exception as e:
            st.error(f"Failed to save animation: {e}")
            return

    if st.button("Play Fireworks"):
        st.write("Playing fireworks...")
        st.image(gif_path, use_container_width=True)
        time.sleep(40)

    if os.path.exists(gif_path):
        os.unlink(gif_path)

if __name__ == "__main__":
    main()

