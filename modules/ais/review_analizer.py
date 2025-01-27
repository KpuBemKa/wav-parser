from logging import getLogger
from traceback import format_exc

import ollama

from modules.singleton_meta import SingletonMeta
from modules.models.issue import Issue, IssueDepartment
from modules.models.review_result import ReviewResult
from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)
#MODEL = "deepseek-r1:1.5b"
MODEL = "llama3.2:3b"


class ReviewAnalizer(metaclass=SingletonMeta):
    def __init__(self, model_name=MODEL) -> None:
        self.__ensure_existence(model_name)

    def summarize_review(self, text: str) -> ReviewResult | None:
       
        try:
            corrected_text = self.__get_corrected_translated(text.replace("  ", " "))
            summarry = self.__get_summary(corrected_text)
            issues = self.__get_issues(corrected_text)

            return ReviewResult(corrected_text, summarry, issues)
        except Exception as ex:
            logger.error(
                f"Exception catched durint audio transcription: {ex} {ex.args}\n{format_exc()}"
            )
            return None

    def __ensure_existence(self, model: str):
        try:
            ollama.chat(model)
        except ollama.ResponseError as e:
            if e.status_code == 404:
                print(f"Model '{model}' not found. Pulling it...")
                ollama.pull(model)
            else:
                print(f"Error: {e.error}")

    def __get_corrected_translated(self, text: str) -> str:
        text = text.strip(" \n")

        corrected = str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to correct the original text of any errors or typos. "
                    "Give me the corrected text wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{text}"
                )
            ).message.content
        )

        return str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to translate the review to English. "
                    "Give me the translated text wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{corrected}"
                )
            ).message.content
        )

    def __get_summary(self, text: str) -> str:
        text = text.strip(" \n")

        return str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to make a short summary of the review. "
                    "Give me the summary wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{text}"
                )
            ).message.content
        )

    def __get_issues(self, text: str) -> list[Issue]:
        text = text.strip(" \n")

        string_issues = str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to make a list of any issues the reviewer may have had with food or service. "
                    "Give me the list of issues in details wihout any additional text, headers, or phrases. "
                    'If you think there are no issues related to restaurants, respond with "None". '
                    "Input review: "
                    f"{text}"
                )
            ).message.content
        ).split("\n")

        result_issues: list[Issue] = []

        for str_issue in string_issues:
            if "None" not in str_issue:
                result_issues.append(Issue(str_issue, self.__get_issue_department(str_issue)))

        return result_issues

    def __get_issue_department(self, issue_description: str) -> IssueDepartment:
        issue_description.strip(" \n")

        departments_str = str(
            self.__execute_prompt(
                (
                    "You are an expert in classifying customer feedback for a restaurant."
                    "Based on the issue I will give you, assign the feedback to the most relevant department. The departments are: "
                    "Kitchen: For issues related to food quality, taste, temperature, preparation, or presentation. "
                    "Floor: For issues related to staff behavior, attentiveness, wait times, table service, and overall customer mood. "
                    "Bar: For issues related to drinks, bartending, cocktails, or bar-specific service. "
                    "Other: For feedback that does not clearly fit into any of the above categories. "
                    "Give me the result wihout any additional text, headers, or phrases. "
                    "Here is the issue: "
                    f"{issue_description}"
                )
            ).message.content
        ).lower()

        # result: list[IssueDepartment] = []

        for department in list(IssueDepartment):
            if department.value in departments_str:
                return department

        return IssueDepartment.OTHER
        # result.append(department)

        # return result

    def __execute_prompt(self, prompt: str) -> ollama.ChatResponse:
        logger.debug(f"Prompting:\n{prompt}\n-----")

        result = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        logger.debug(f"Response:\n{result.message.content}\n-----")

        return result


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
