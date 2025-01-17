import logging
from enum import Enum

import ollama

from modules.singleton_meta import SingletonMeta
from settings import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)
MODEL = "llama3.2:3b"


class IssueDepartment(Enum):
    FLOOR = "floor"
    KITCHEN = "kitchen"
    BAR = "bar"
    OTHER = "other"


class Issue:
    def __init__(self, description: str, department: IssueDepartment) -> None:
        self.description = description
        self.department = department


class AnalizerResult:
    def __init__(self, corrected_text: str, summary: str, issues: list[Issue]) -> None:
        self.corrected_text = corrected_text
        self.summary = summary
        self.issues = issues


class ReviewAnalizer(metaclass=SingletonMeta):
    def __init__(self, model_name=MODEL) -> None:
        self.__ensure_existence(model_name)

    def summarize_review(self, text: str) -> AnalizerResult:
        self.__ensure_existence(MODEL)

        corrected_text = self.__get_corrected(text)
        summarry = self.__get_summary(corrected_text)
        issues = self.__get_issues(corrected_text)

        return AnalizerResult(corrected_text, summarry, issues)

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
        text = text.strip(" \n")

        return str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to correct the original text of any errors or typos. "
                    "Give me the corrected text wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{text}"
                ).strip(" \n")
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
                ).strip(" \n")
            ).message.content
        )

    def __get_issues(self, text: str) -> list[Issue]:
        text = text.strip(" \n")

        string_issues = str(
            self.__execute_prompt(
                (
                    "I will give you a review for a restaurant. "
                    "I want you to make a list of any issues the reviewer may have had with food or service. "
                    "Give me the list wihout any additional text, headers, or phrases. "
                    "Input review: "
                    f"{text}"
                ).strip(" \n")
            ).message.content
        ).split("\n")

        result_issues: list[Issue] = []

        for str_issue in string_issues:
            result_issues.append(Issue(str_issue, self.__get_issue_department(str_issue)))

        return result_issues

    def __get_issue_department(self, issue_description: str) -> IssueDepartment:
        issue_description.strip(" \n")

        return IssueDepartment(
            str(
                self.__execute_prompt(
                    (
                        "I will give you an issue with a restaurant which was experienced by a visitor. "
                        "I want you to categorize this issue to one of these departments: Floor, Kitchen, Bar, Other. "
                        "Give me the department you think is responsible and can fix this issue. "
                        "Give me the result wihout any additional text, headers, or phrases. "
                        "Input issue: "
                        f"{issue_description}"
                    ).strip(" \n")
                ).message.content
            ).lower()
        )

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
