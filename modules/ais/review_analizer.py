import json
from logging import getLogger

import ollama

from modules.singleton_meta import SingletonMeta
from modules.models.issue import Issue, IssueDepartment
from settings import LOGGER_NAME


logger = getLogger(LOGGER_NAME)
MODEL = "llama3.2:3b"


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
        # text = text.strip(" \n")

        # string_issues = str(
        #     self.__execute_prompt(
        #         (
        #             "I will give you a review for a restaurant. "
        #             "I want you to make a list of any issues the reviewer may have had with food or service. "
        #             "Give me the list wihout any additional text, headers, or phrases. "
        #             'If you think there are no issues related to restaurants, respond with "None". '
        #             "Input review: "
        #             f"{text}"
        #         ).strip(" \n")
        #     ).message.content
        # ).split("\n")

        # result_issues: list[Issue] = []

        # for str_issue in string_issues:
        #     if "None" not in str_issue:
        #         result_issues.append(Issue(str_issue, self.__get_issue_department(str_issue)))

        # return result_issues

        issues_str = self.__execute_prompt(
            (
                "You are an AI assistant tasked with analyzing restaurant reviews.\n"
                "Instructions:\n"
                "1. Read the customer's review carefully.\n"
                "2. Identify any problems mentioned, and categorize them under the following tags:\n"
                '   - "floor": Problems related to the dining area, such as lighting, atmosphere, seating, etc.\n'
                '   - "kitchen": Problems related to food, such as being too salty, too sweet, undercooked, etc.\n'
                '   - "bar": Problems related to beverages or the bar area.\n'
                '   - "others": Problems that do not fit into the above categories.\n'
                "3. For each category that has at least one problem, create a key in the JSON object with an array of strings describing each specific issue.\n"
                "4. If there are no problems for a given category, do not include that category in the output.\n"
                "5. If there are no problems whatsoever, return an empty JSON object: {}.\n"
                "6. Important: Output only the JSON—no extra explanation, comments, or text outside the JSON.\n"
                "Example:\n"
                'Review: "The dining area was way too hot, and the soup tasted bland. The drinks were fine, though."\n'
                "A correct output would be:\n"
                '{"floor": "The dining area was way too hot", "kitchen": "The soup tasted bland"}'
            )
        ).message.content

        return [
            Issue(description, IssueDepartment(department))
            for department, description in json.loads(
                issues_str if issues_str is not None else "{}"
            ).items()
        ]

    # def __get_issue_department(self, issue_description: str) -> list[IssueDepartment]:
    #     issue_description.strip(" \n")

    #     departments_str = str(
    #         self.__execute_prompt(
    #             (
    #                 # "I will give you an issue with a restaurant which was experienced by a visitor. "
    #                 # "I want you to select some of these departments you think are the most responsible and can fix this issue: "
    #                 # "Guest Area, Kitchen, Bar, Other. "
    #                 # "Give me the result wihout any additional text, headers, or phrases. "
    #                 # "Input issue: "
    #                 "You are an expert in classifying customer feedback for a restaurant. Based on the issue I will give you, assign the feedback to the most relevant department. The departments are: "
    #                 "Kitchen: For issues related to food quality, taste, temperature, preparation, or presentation. "
    #                 "Guest area: For issues related to staff behavior, attentiveness, wait times, table service, and overall customer mood. "
    #                 "Bar: For issues related to drinks, bartending, cocktails, or bar-specific service. "
    #                 "Other: For feedback that does not clearly fit into any of the above categories. "
    #                 "Give me the result wihout any additional text, headers, or phrases. "
    #                 "Here is the issue: "
    #                 f"{issue_description}"
    #             ).strip(" \n")
    #         ).message.content
    #     ).lower()

    #     result: list[IssueDepartment] = []

    #     for department in list(IssueDepartment):
    #         if department.value in departments_str:
    #             result.append(department)

    #     return result

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
