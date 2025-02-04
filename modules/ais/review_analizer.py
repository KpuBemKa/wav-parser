from logging import getLogger
from traceback import format_exc
# from time import time as getTime

import ollama

from modules.singleton_meta import SingletonMeta
from modules.models.issue import Issue, IssueDepartment
from modules.models.review_result import ReviewResult
from settings import (
    LOGGER_NAME,
    OLLAMA_MODEL,
    CORRECTION_PROMPT,
    TRANSLATE_PROMPT,
    SUMMARIZE_PROMPT,
    GET_ISSUES_PROMPT,
    ISSUES_DEPARTMENTS_PROMPT,
)


logger = getLogger(LOGGER_NAME)


class ReviewAnalizer(metaclass=SingletonMeta):
    def __init__(self, model_name=OLLAMA_MODEL) -> None:
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
        corrected = str(self.__execute_prompt(f"{CORRECTION_PROMPT}{text}").message.content)
        return str(self.__execute_prompt(f"{TRANSLATE_PROMPT}{corrected}").message.content)

    def __get_summary(self, text: str) -> str:
        text = text.strip(" \n")
        return str(self.__execute_prompt(f"{SUMMARIZE_PROMPT}{text}").message.content)

    def __get_issues(self, text: str) -> list[Issue]:
        text = text.strip(" \n")
        string_issues = str(
            self.__execute_prompt(f"{GET_ISSUES_PROMPT}{text}").message.content
        ).split("\n")

        result_issues: list[Issue] = []
        for str_issue in string_issues:
            if "None" not in str_issue:
                result_issues.append(Issue(str_issue, self.__get_issue_department(str_issue)))

        return result_issues

    def __get_issue_department(self, issue_description: str) -> IssueDepartment:
        issue_description.strip(" \n")

        departments_str = str(
            self.__execute_prompt(f"{ISSUES_DEPARTMENTS_PROMPT}{issue_description}").message.content
        ).lower()

        for department in list(IssueDepartment):
            if department.value in departments_str:
                return department

        return IssueDepartment.OTHER

    def __execute_prompt(self, prompt: str) -> ollama.ChatResponse:
        logger.debug(f"Prompting:\n{prompt}\n-----")

        result = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        logger.debug(f"Response:\n{result.message.content}\n-----")

        return result
