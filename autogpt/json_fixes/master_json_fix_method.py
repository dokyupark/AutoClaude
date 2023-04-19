import re
from typing import Any, Dict

from autogpt.config import Config
from autogpt.logs import logger
from autogpt.speech import say_text

CFG = Config()

def fix_linebreaker(match):
    first = match.group(1)
    last = match.group(3)
    if first == "{" or first == "[" or first == '"':
        return match.group()
    if last == "}" or last == "]" or last == '"':
        return match.group()
    return first + "\\n" + last

def fix_bracers(text):
    def fix1(m):
        return m.group(1) + '"'
    def fix2(m):
        return '"' + m.group(2)
    def fix3(m):
        return '"' + m.group(2) + '"'

    text = re.sub(r'"', '\\"', text);
    text = re.sub(r'([\{\[][\s\t\r\n]*)(\'|\\+")', fix1, text)
    text = re.sub(r'(\'|\\+")([\s\t\r\n]*[\}\]])', fix2, text)
    text = re.sub(r'([\}\]][\s\t\r\n]*,[\s\t\r\n]*)(\'|\\+")', fix1, text)
    text = re.sub(r'(\'|\\+")([\s\t\r\n]*[,:][\s\t\r\n]*[\{\[])', fix2, text)
    text = re.sub(r'(\'|\\*")([:,][\s\t\r\n]*)(\'|\\*")', fix3, text)
    return text

def prefix_json(text: str) -> str:
    loc = text.index('{')
    if loc != 0:
        text = text[loc:]

    text = fix_bracers(text)

    text = re.sub(r'(.)([ \s\t]*[\r\n][ \s\t]*)+(.)', fix_linebreaker, text)
    return text

def fix_json_using_multiple_techniques(assistant_reply: str) -> Dict[Any, Any]:
    from autogpt.json_fixes.parsing import (
        attempt_to_fix_json_by_finding_outermost_brackets,
        fix_and_parse_json,
    )

    # Parse and print Assistant response
    assistant_reply_json = fix_and_parse_json(assistant_reply)
    if assistant_reply_json == {}:
        assistant_reply_json = attempt_to_fix_json_by_finding_outermost_brackets(
            assistant_reply
        )

    if assistant_reply_json != {}:
        return assistant_reply_json

    logger.error(
        "Error: The following AI output couldn't be converted to a JSON:\n",
        assistant_reply,
    )
    if CFG.speak_mode:
        say_text("I have received an invalid JSON response from the OpenAI API.")

    return {}
