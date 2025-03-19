import streamlit as st
from textblob import TextBlob
import pandas as pd
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
import pytz

# Define the America/Chicago time zone
CHICAGO_TZ = pytz.timezone("America/Chicago")

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

st.title("📔 Daily Mood Diary")
st.write("Document your daily mood with two sentences!")

# Collapsible upload block
show_upload = st.checkbox("Upload custom mood history")
uploaded_file = None
if show_upload:
    uploaded_file = st.file_uploader("Upload your mood history CSV", type=["csv"])

# Initialize or load data
if uploaded_file is not None:
    try:
        # Load the uploaded file into a DataFrame
        st.session_state.mood_history = pd.read_csv(uploaded_file, parse_dates=["Date"])
        
        # Ensure the Date column is timezone-aware in Chicago time
    
        
        # Save the DataFrame to the server, replacing the existing file
        st.session_state.mood_history.to_csv(CSV_FILE, index=False)
        st.success(f"File '{CSV_FILE}' has been successfully replaced with the uploaded data.")
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    if os.path.exists(CSV_FILE):
        st.session_state.mood_history = pd.read_csv(CSV_FILE, parse_dates=["Date"])
        # Ensure the Date column is timezone-aware in Chicago time
        
    else:
        st.session_state.mood_history = pd.DataFrame(columns=[
            "Date", "Sentence 1", "Sentence 2", 
            "Predicted Mood", "Mood Score", "Emoji"
        ])

st.write("## Daily Entry")

# Determine if today's entry exists
today_date = datetime.now(CHICAGO_TZ).date()  # Use Chicago time zone
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
    today = datetime.now(CHICAGO_TZ)  # Use Chicago time zone
    
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
    col1, col2, col3 = st.columns(3)
    today_entry = st.session_state.mood_history.iloc[-1]
    with col1:
        st.metric("Predicted Mood", f"{today_entry['Predicted Mood']} {today_entry['Emoji']}")
    with col2:
        st.metric("Mood Score", f"{today_entry['Mood Score']:.2f}")
    with col3:
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
    display_df["Date"] = display_df["Date"].dt.tz_convert(CHICAGO_TZ).dt.strftime("%Y-%m-%d")  # Convert to Chicago time
    st.dataframe(display_df.style.format({"Mood Score": "{:.2f}"}))

    st.subheader("Mood Timeline (Current Month)")
    now_chicago = datetime.now(CHICAGO_TZ)
    current_month = now_chicago.month
    current_year = now_chicago.year

    # Generate a full range of dates for the current month
    start_of_month = datetime(current_year, current_month, 1, tzinfo=CHICAGO_TZ)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    full_month_dates = pd.date_range(start=start_of_month, end=end_of_month, freq='D')

    # Create a DataFrame with the full month of dates
    full_month_df = pd.DataFrame({"Date": full_month_dates})

    # Merge mood history with the full month of dates
    monthly_data = pd.merge(full_month_df, st.session_state.mood_history, on="Date", how="left")
    monthly_data["Date"] = monthly_data["Date"].dt.tz_convert(CHICAGO_TZ)

    if not monthly_data.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(monthly_data["Date"], monthly_data["Mood Score"], 
                marker='o', linestyle='-', color='skyblue', label="Mood Score")
        
        for date, score, emoji in zip(monthly_data["Date"], monthly_data["Mood Score"], monthly_data["Emoji"]):
            if pd.notnull(score):  # Only plot emojis for non-NaN scores
                ax.text(date, score + 0.02, emoji, fontsize=12, ha='center', va='bottom', color="orange")
        
        # Format the X-axis to show all days of the month
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d'))  # Format as day of month
        plt.xticks(rotation=45)
        ax.set_xlabel("Day of Month")
        ax.set_ylabel("Mood Score")
        ax.set_title(f"Mood Timeline ({now_chicago.strftime('%B %Y')})")  # Use Chicago time zone
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.info("No data available for the current month.")

st.markdown("---")
st.caption("Your personal mood diary - Reflect, remember, and grow.")

