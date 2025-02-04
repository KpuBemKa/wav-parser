from pathlib import Path
from logging import DEBUG as logging_DEBUG
# from logging import INFO as loggin_INFO

# LOG_LEVEL = loggin_INFO
LOG_LEVEL = logging_DEBUG
LOGGER_NAME = "logging"

# log message format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(module)s - %(message)s"

# the folder in which data from esps is stored
RECORDINGS_FOLDER = "esp-recordings"

# DELETE_CONVERTED_FILES = True
DELETE_CONVERTED_FILES = False

ALLOWED_EXTENSIONS = [".wav", ".mp3", ".ogg", ".m4a"]

ODOO_URL = "http://139.59.88.189:8069"
ODOO_UPLOAD_ENDPOINT = f"{ODOO_URL}/rvg/new_rec"

# Path to store audio files
TELEGRAM_AUDIO_DIR = Path("./home/telegram-recordings/")
if not TELEGRAM_AUDIO_DIR.exists():
    TELEGRAM_AUDIO_DIR.mkdir()


WHISPER_MODEL = "openai/whisper-large-v3"
OLLAMA_MODEL = "mistral:7b-instruct-v0.3-q5_K_M"

CORRECTION_PROMPT = (
    
    "You are a highly capable AI assistant. You excel at reviewing text for grammar, punctuation, and clarity, while preserving the text’s original meaning and context. "

    "Task: You are given a piece of text that was transcribed by OpenAI Whisper. Your job is to correct and refine this text by: "

    "Fixing grammar and spelling errors. "
    "Improving punctuation and sentence structure. "
    "Preserving the original meaning. "
    "Please provide the corrected version of the text in a clear, coherent format. "
    
    #"I will give you a review for a restaurant. "
    #"I want you to correct the original text of any errors or typos. "
    #"Give me the corrected text wihout any additional text, headers, or phrases. "
    "Input review: "
)

TRANSLATE_PROMPT = (
    
    
    "You are a highly capable, multilingual AI assistant. You excel at accurately translating text reviews from various languages into clear, natural-sounding English. "
    "Task: Translate the following text into fluent, easily understandable English. Make sure the meaning, tone, and intent remain accurate. If a cultural reference or nuance appears, please convey it clearly in English. "
    #"I will give you a review for a restaurant. "
    #"I want you to translate the review to English. "
    #"Give me the translated text wihout any additional text, headers, or phrases. "
    "Input review: "
)

SUMMARIZE_PROMPT = (
    
    "You are a helpful AI assistant. You excel at reading and summarizing user-provided text, highlighting key points, sentiment, and recommendations. "

    "Task: Analyze the following review from a customer about their experience at a cafe/restaurant. Then provide a concise summary that covers these points: "

    "Key Details: Main aspects of the review (e.g., food quality, service, ambiance). "
    "Positive Feedback: What did the customer like? "
    "Negative Feedback: What complaints or issues did they mention? "
    "Overall Sentiment: General tone or feeling (e.g., positive, mixed, negative). "
    "Recommendations (if applicable): Any suggestions for improvement. "
    
    "The summary should be clear, concise, and written in everyday language. Aim for 3-5 sentences or a short bulleted list. "
    
    #"I will give you a review for a restaurant. "
    #"I want you to make a short summary of the review. "
    #"Give me the summary wihout any additional text, headers, or phrases. "
    "Input review: "
)

GET_ISSUES_PROMPT = (
    #"I will give you a review for a restaurant. "
    #"I want you to make a list of any issues the reviewer may have had with food or service. "
    #"Give me the list of issues in details wihout any additional text, headers, or phrases. "
    #'If you think there are no issues related to restaurants, respond with "None". '
    
    "You are a detail-oriented AI assistant. Your job is to identify and list any problems or issues mentioned in a customer’s review about a cafe or restaurant. "
    "Task: Analyze the following review and create a clear list of problems without any extra commentary or explanation, do not duplicate issues on the list. If there are no problems, respond with “None” (exactly and nothing else). "
    "Input review: "
)

ISSUES_DEPARTMENTS_PROMPT = (
    "You are an expert in classifying customer feedback for a restaurant."
    "Based on the issue I will give you, assign the feedback to the most relevant department. The departments are: "
    "Kitchen: For issues related to food quality, taste, temperature, preparation, or presentation. "
    "Floor: For issues related to staff behavior, attentiveness, wait times, table service, and overall customer mood. "
    "Bar: For issues related to drinks, bartending, cocktails, or bar-specific service. "
    "Other: For feedback that does not clearly fit into any of the above categories. "
    "Give me the result wihout any additional text, headers, or phrases. "
    "Here is the issue: "
)
