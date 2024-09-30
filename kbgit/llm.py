import re
from openai import OpenAI # type: ignore
from ollama import chat as ollama_chat # type: ignore
import os
from .log import logger
from .prompts.kbb import (
    PROMPT_KBB_REWRITE, 
    PROMPT_KBB_SUB, 
    PROMPT_KBB_CONFLICTS, 
    PROMPT_KBB_CORRECT
)


def get_embedding(text: str, model : str = "text-embedding-3-small") -> list:
    """
    Retrieve the embedding for a given text using the specified model.

    Args:
        text (str): The input text for which to generate the embedding.
        model (str, optional): The embedding model to use. 
            Defaults to "text-embedding-3-small".

    Returns:
        list: A list representing the embedding vector for the input text. 
              Returns a list of zeros if the input text is empty.
    """
    # TODO. Add support for other embedding models. 
    if len(text) > 0:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        emb_output = client.embeddings.create(
            input = [text], 
            model = model
        ).data[0].embedding
        return emb_output
    else:
        EMBEDDING_OUTPUT_SIZE = os.getenv("EMBEDDING_OUTPUT_SIZE")
        if (EMBEDDING_OUTPUT_SIZE is None) or (EMBEDDING_OUTPUT_SIZE == ""):
            emb_output_size = 1
        else:
            emb_output_size = int(EMBEDDING_OUTPUT_SIZE)
        return [0] * emb_output_size




def make_llm_call(text: str, expected: str = "", attempts: int = 3) -> str:
    """    
    Makes a call to a specified LLM provider to obtain a response.

    Args:
        text (str): The input text to send to the LLM.
        expected (str, optional): A substring that the response is expected 
            to contain. Defaults to "".
        attempts (int, optional): The number of attempts to make if the 
            first response does not meet expectations. Defaults to 3.

    Returns:
        str: The response content from the LLM. If none of the attempts 
            yield a response containing the expected substring, 
            it returns the last response content obtained or an empty string 
            if no response was received.
    """    
    # TODO. Add support for other LLM providers. 
    # TODO. More customizations. 
    # TODO. Better expected checks (not only strings).
    #text = text.replace("\n", " ")
    llm_provider = os.getenv("LLM_PROVIDER")
    response_content = ""

    logger.debug("LLM CALL: " + text)

    if llm_provider == "OPENAI":
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        for _ in range(attempts):
            if _ > 0:
                logger.warning(
                    f"Attempt #{_} to obtain an acceptable answer from the LLM."
                )
            response = client.chat.completions.create(
                model=os.getenv('OPEN_API_MODEL'),
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type": "text", 
                                "text": text
                            }
                        ]
                    }
                ],
                temperature=1,
                max_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                response_format={"type": "text"},
            )
            response_content = response.choices[0].message.content
            logger.debug("LLM ANSWER: " + response_content)
            if expected in response_content:
                return response_content

    elif llm_provider == "OLLAMA":
        for _ in range(attempts):
            if _ > 0:
                logger.warning(
                    f"Attempt #{_} to obtain an acceptable answer from the LLM."
                )
            response_content = ollama_chat(
                model = os.getenv("OLLAMA_MODEL"),
                messages = [
                    {
                        "role": "user", 
                        "content": text,
                    },
                ]
            )["message"]["content"]
            logger.debug("LLM ANSWER: " + response_content)
            if expected in response_content:
                return response_content
    
    return response_content


def parse_output(
    text: str, 
    pattern: str = r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'
) -> str:
    """
    Extracts the text enclosed within a specific output pattern 
    from the given text.

    This function searches for patterns in the input text that match a specified
    regular expression and returns the last match found. If no matches are 
    found, a warning is logged and an empty string is returned.

    Args:
        text (str): The input text from which to extract the output. 
        pattern (str, optional): A regular expression pattern to identify 
            the output. Defaults to r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'.

    Returns:
        str: The extracted text found within the specified pattern. 
            Returns an empty string if no matches are found.
    """
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        extracted_text = matches[-1].strip()
        return extracted_text 
    logger.warning(
        f"Pattern not found. Returning empty string. " + \
        f"Unparsed output: {text}"
    )
    return ""
    

def llm_text_rewrite(
    text: str, 
    expected: str = "<OUTPUT>", 
    pattern: str = r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'
) -> dict:
    """
    Rewrite the provided text using a language model, handling potential 
    conflicts and extracting processed output.

    This function makes a call to a language model with the provided text 
    and attempts to rewrite it. If conflicts are detected in the parsed output, 
    it will correct these conflicts and provide the corrected output.
    It returns both the raw output from the model and the parsed output 
    extracted from that raw output.

    Args:
        text (str): The input text that needs to be rewritten.
        expected (str, optional): A tag indicating the expected output format. 
            Defaults to "<OUTPUT>".
        pattern (str, optional): A regular expression pattern to identify the 
            output in the response. 
            Defaults to r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'.

    Returns:
        dict: A dictionary containing:
            - "raw_output" (str): The raw output received from the 
              language model.
            - "parsed_output" (str): The extracted and potentially corrected 
              output from the raw response.
    """
    raw_output = make_llm_call(
        text=PROMPT_KBB_REWRITE % (text), 
        expected=expected
    )
    parsed_output = parse_output(
            text= raw_output,
            pattern=pattern
        )
    conflicts = llm_conflicts_detect(parsed_output)["parsed_output"]
    if conflicts:
        dict_corrected_output = llm_correct(
            text=parsed_output, 
            comment=conflicts
        )
        raw_output = raw_output + dict_corrected_output["raw_output"]
        parsed_output = dict_corrected_output["parsed_output"]
    return {
        "raw_output": raw_output,
        "parsed_output": parsed_output
    }


def llm_text_remove(
    text1: str, text2: str, 
    expected: str = "<OUTPUT>", 
    pattern: str = r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'
) -> dict:
    """
    Remove contents of text2 from text1 using a language model.

    This function calls a language model to process the provided texts, 
    attempting to remove `text2` from `text1`. If conflicts are detected 
    in the parsed output, it corrects these conflicts and compiles the results. 
    The function returns both the raw output from the model and the processed 
    output.

    Args:
        text1 (str): The primary text from which occurrences of text2 will be 
            removed.
        text2 (str): The text that needs to be removed from text1.
        expected (str, optional): A tag indicating the expected output format. 
            Defaults to "<OUTPUT>".
        pattern (str, optional): A regular expression pattern to identify the 
            output in the response. 
            Defaults to r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'.

    Returns:
        dict: A dictionary containing:
            - "raw_output" (str): The raw output received from the language 
              model.
            - "parsed_output" (str): The extracted and potentially corrected 
              output from the raw response.
    """
    raw_output = make_llm_call(
        text=PROMPT_KBB_SUB % (text1, text2), 
        expected=expected
    )
    parsed_output = parse_output(
            text= raw_output,
            pattern=pattern
        )
    conflicts = llm_conflicts_detect(parsed_output)["parsed_output"]
    if conflicts:
        dict_corrected_output = llm_correct(
            text=parsed_output, 
            comment=conflicts
        )
        raw_output = raw_output + dict_corrected_output["raw_output"]
        parsed_output = dict_corrected_output["parsed_output"]
    return {
        "raw_output": raw_output,
        "parsed_output": parsed_output
    }


def llm_conflicts_detect(
    text: str, 
    expected: str = "<OUTPUT>", 
    pattern: str = r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'
) -> dict:
    """
    Detect potential conflicts in the provided text using a language model.

    This function utilizes a language model to analyze the input text for any 
    conflicting statements or contradictions. If no conflicts are detected, it 
    returns a result indicating that there are no issues. If potential conflicts 
    are found, it logs a warning and returns the details of the conflicts.

    Args:
        text (str): The input text to be analyzed for conflicts.
        expected (str, optional): A tag indicating the expected output format. 
            Defaults to "<OUTPUT>".
        pattern (str, optional): A regular expression pattern to identify the 
            output in the response. 
            Defaults to r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'.

    Returns:
        dict: A dictionary containing:
            - "raw_output" (str): The raw output received from the language 
              model.
            - "parsed_output" (bool or str): 
                - `False` if no conflicts are found (indicating that everything 
                  is OK), 
                - or the parsed output string containing details of potential 
                  conflicts if any are detected.
    """
    raw_output = make_llm_call(
        text=PROMPT_KBB_CONFLICTS % (text), 
        expected=expected
    )
    parsed_output = parse_output(
        text=raw_output,
        pattern=pattern
    )
    if (parsed_output == "OK") or \
        ("no contradiction" in parsed_output) or \
        ("no evident contradictory" in parsed_output) or \
        ("no contradictory" in parsed_output):
        return {
            "raw_output": raw_output, 
            "parsed_output": False
        }
    else: 
        logger.warning(f"Possible conflicts in the text: {parsed_output}")
        return {
            "raw_output": raw_output, 
            "parsed_output": parsed_output
        }
    

def llm_correct(
    text: str, comment: str, 
    expected: str = "<OUTPUT>", 
    pattern: str = r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'
) -> dict:
    """
    Correct the given input text using a language model.

    This function utilizes a language model to correct the provided input text
    based on the provided comment. It returns both its raw output and processed 
    output.

    Args:
        text (str): The input text that needs correction.
        comment (str): A string containing the comment explaining the potential 
            issues in the given text.
        expected (str, optional): A tag indicating the expected output format. 
            Defaults to "<OUTPUT>".
        pattern (str, optional): A regular expression pattern to identify the 
            output in the response. 
            Defaults to r'\<OUTPUT\>\s*(.*?)\s*\</OUTPUT\>'.

    Returns:
        dict: A dictionary containing:
            - "raw_output" (str): The raw output received from the language 
              model.
            - "parsed_output"  (str): The corrected string.
    """
    raw_output = make_llm_call(
        text=PROMPT_KBB_CORRECT % (text, comment), 
        expected=expected
    )
    parsed_output = parse_output(
        text=raw_output,
        pattern=pattern
    )
    return {
        "raw_output": raw_output,
        "parsed_output": parsed_output
    }
