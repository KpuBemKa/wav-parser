import ollama


MODEL = "llama3.2:3b"


class SummarizerResult:
    def __init__(self, corrected_text, summary, issues) -> None:
        self.corrected_text = corrected_text
        self.summary = summary
        self.issues = issues


class Summarizer:
    def __init__(self) -> None:
        pass

    def summarize_text(self, text: str) -> SummarizerResult:
        self.__ensure_existence(MODEL)

        corrected_text = self.__get_corrected(text)
        # print(f"\nCorrected review:\n{corrected_text}\n---")

        summarry = self.__get_summary(text)
        # print(f"\nReview summary:\n{summarry}\n---")

        issues = self.__get_issues(text)
        # print(f"\nReview issues:\n{issues}\n---")

        return SummarizerResult(corrected_text, summarry, issues)

    def __ensure_existence(self, model: str):
        try:
            ollama.chat(model)
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"Model '{model}' not found. Pulling it...")
                ollama.pull(model)
            else:
                print(f"Error: {e.error}")

    def __get_corrected(self, text: str) -> str:
        return str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to correct the original text of any errors or typos. "
                    "Give me the corrected text wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{text}"
                ).strip(" ")
            ).message.content
        )

    def __get_summary(self, text: str) -> str:
        return str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to make a short summary of the review. "
                    "Give me the summary wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{text}"
                ).strip(" ")
            ).message.content
        )

    def __get_issues(self, text: str) -> str:
        return str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to make a list of any issues the reviewer may have had with food or service. "
                    "Give me the list wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{text}"
                ).strip(" ")
            ).message.content
        )

    def __execute_prompt(self, prompt: str) -> ollama.ChatResponse:
        return ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )


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
