import time
import openai
from colorama import Fore
from config import Config

# Claude
MAX_TOKEN_ONCE = 4096
CONTINUE_PROMPT = "... continue"
import anthropic

cfg = Config()

openai.api_key = cfg.openai_api_key

def _sendReq(client, prompt, max_tokens_to_sample):
    response = client.completion(
        prompt=prompt,
        stop_sequences = [anthropic.HUMAN_PROMPT, anthropic.AI_PROMPT],
        model=cfg.claude_mode,
        max_tokens_to_sample=max_tokens_to_sample,
    )
    return response

def sendReq(question, max_tokens_to_sample: int = MAX_TOKEN_ONCE):
    client = anthropic.Client(cfg.claude_api_key)
    prompt = f"{anthropic.HUMAN_PROMPT} {question} {anthropic.AI_PROMPT}"

    response = _sendReq(client, prompt, max_tokens_to_sample)
    data = response["completion"]
    prompt = prompt + response["completion"]

    while response["stop_reason"] == "max_tokens":
        prompt = prompt + f"{anthropic.HUMAN_PROMPT} {CONTINUE_PROMPT} {anthropic.AI_PROMPT}"
        response = _sendReq(client, prompt, max_tokens_to_sample)
        d = response["completion"]
        prompt = prompt + d
        if data[-1] != ' ' and d[0] != ' ':
            data = data + " " + d
        else:
            data = data + d
    return data

# Overly simple abstraction until we create something better
# simple retry mechanism when getting a rate error or a bad gateway
def create_chat_completion(messages, model=None, temperature=cfg.temperature, max_tokens=None)->str:
    """Create a chat completion using the OpenAI API"""
    response = None
    num_retries = 5
    for attempt in range(num_retries):
        try:
            if cfg.use_claude:
                response = sendReq(messages)
            elif cfg.use_azure:
                response = openai.ChatCompletion.create(
                    deployment_id=cfg.get_azure_deployment_id_for_model(model),
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            break
        except openai.error.RateLimitError:
            if cfg.debug_mode:
                print(Fore.RED + "Error: ", "API Rate Limit Reached. Waiting 20 seconds..." + Fore.RESET)
            time.sleep(20)
        except openai.error.APIError as e:
            if e.http_status == 502:
                if cfg.debug_mode:
                    print(Fore.RED + "Error: ", "API Bad gateway. Waiting 20 seconds..." + Fore.RESET)
                time.sleep(20)
            else:
                raise
            if attempt == num_retries - 1:
                raise

    if response is None:
        raise RuntimeError("Failed to get response after 5 retries")

    if cfg.use_claude:
        return response
    else:
        return response.choices[0].message["content"]
