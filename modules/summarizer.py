import ollama


MODEL = "llama3.2:3b"


class Summarizer:
    def __init__(self) -> None:
        pass

    def summarize_text(self, text: str) -> str:
        self.__ensure_existence(MODEL)
        
        propmt = (
            "Summarize this next restaurant review into a list of bullet points. "
            "Just a bullet list, no additional text. "
            f'The review: "{text}"'
        )

        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": propmt,
                }
            ],
        )

        return response["message"]["content"]

    def __ensure_existence(self, model: str):
        try:
            ollama.chat(model)
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"Model '{model}' not found. Pulling it...")
                ollama.pull(model)
            else:
                print(f"Error: {e.error}")


# # MODEL = "llama3.1:8b"
# MODEL = "llama3.2:3b"

# ensure_existance(MODEL)

# with open("home/telegram-recordings/tg@mxridman_1737027637_en.txt", "r") as txt_file:
#     propmt = (
#         "Summarize this next restaurant review into a list of bullet points. "
#         "Just a bullet list, no additional text. "
#         f'The review: "{txt_file.read()}"'
#     )

#     response = ollama.chat(
#         model=MODEL,
#         messages=[
#             {
#                 "role": "user",
#                 "content": propmt,
#             }
#         ],
#     )

#     print(response["message"])
#     print("")
#     print(response["message"]["content"])
