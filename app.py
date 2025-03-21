import os
from langchain.chains import LLMChain
from langchain.core.prompts import PromptTemplate
from langchain.llms import ChatGroq
from googleapiclient.discovery import build
import gradio as gr
import html  # For sanitizing user input

# Load API keys securely from Hugging Face Secrets
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not GROQ_API_KEY or not YOUTUBE_API_KEY:
    raise ValueError("❌ API keys are missing! Please add them in Hugging Face Secrets.")

# Initialize the Groq model
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=GROQ_API_KEY)

# Prompt Template
prompt_template = PromptTemplate(
    input_variables=["user_input", "age_range"],
    template=(
        "**{user_input}**\n\n"
        "The user's selected age range is: **{age_range}**.\n\n"
        "Use Chain-of-Thought (CoT) reasoning to analyze the situation in context with the age range, then provide "
        "clear, actionable safety advice structured as follows:\n\n"
        "**### 🛡️Safety Tips 🛡️**\n"
        "- Offer **practical** and **actionable** steps to stay safe, tailored to the selected age range.\n"
        "- Ensure the advice is **easy to follow** and **relevant** to the situation described.\n\n"
        "**### 🛡️Self-Defense Techniques 🛡️**\n"
        "- Provide simple, **age-appropriate self-defense methods** that are easy to implement.\n"
        "- Focus on **safe** and **effective** techniques that suit the user's age and physical abilities.\n\n"
        "**### 🛡️Resources 🛡️**\n"
        "- Recommend **relevant YouTube videos** for learning and practical demonstrations of safety measures."
    )
)

# Create the LLMChain
chain = LLMChain(llm=llm, prompt=prompt_template)

# Function to fetch YouTube videos with clickable links
def search_youtube_videos(query, max_results=2):
    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            part="snippet", q=query, type="video", maxResults=max_results
        )
        response = request.execute()
        video_html = "<h3>🎥 Recommended Videos:</h3><ul>"
        for item in response.get("items", []):
            video_id = item["id"].get("videoId")
            video_title = html.escape(item["snippet"].get("title", "Untitled"))
            if video_id:
                video_html += f'<p><a href="https://www.youtube.com/watch?v={video_id}" target="_blank">{video_title}</a></p>'
        return video_html if video_html else "<p>No relevant videos found.</p>"
    except Exception as e:
        return f"<p>⚠️ Error fetching videos: {html.escape(str(e))}</p>"

# Function to get YouTube links based on age range
def get_youtube_links(age_range):
    queries = {
        "0-6 (Toddler)": "toddler safety self-defense techniques",
        "7-13 (Child)": "self-defense for kids",
        "15-30 (Teenager to Young Adult)": "basic self-defense techniques for teens",
        "30+ (Adult)": "advanced self-defense techniques for adults"
    }
    return search_youtube_videos(queries.get(age_range, "self-defense safety tips"), max_results=2)

# Safety Advice Function
def safety_advice(user_input, age_range):
    if not user_input.strip():
        return "⚠️ Please enter a situation to receive advice.", "<p></p>"  # Empty HTML for videos

    response = chain.run(user_input=user_input, age_range=age_range)
    links_html = get_youtube_links(age_range)

    return f"{response}", links_html  # Markdown for text, HTML for videos

# Function to clear fields
def clear_fields():
    return "", "30+ (Adult)", "", ""

# Gradio Interface
with gr.Blocks() as app:
    gr.Markdown("# 🛡️ SheGuard: Personal Safety Advisor 🛡️\n\n💡 Enter a situation where you feel unsafe, and receive expert safety advice tailored to your age range.")

    with gr.Row():
        situation_input = gr.Textbox(label="Describe Your Situation", placeholder="E.g., I noticed someone suspicious near my house.")
        age_range_input = gr.Radio([
            "0-6 (Toddler)", "7-13 (Child)", "15-30 (Teenager to Young Adult)", "30+ (Adult)"
        ], label="Select Your Age Range", value="30+ (Adult)")

    advice_output = gr.Markdown()
    video_output = gr.HTML()  # Using HTML for active YouTube links

    with gr.Row():
        generate_button = gr.Button("Get Safety Advice")
        clear_button = gr.Button("Clear")

    generate_button.click(safety_advice, inputs=[situation_input, age_range_input], outputs=[advice_output, video_output])
    clear_button.click(clear_fields, inputs=[], outputs=[situation_input, age_range_input, advice_output, video_output])

app.launch(share = True)