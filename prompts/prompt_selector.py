from langchain.prompts import PromptTemplate
def prompt_sector(position: str, prompts: classmethod) -> dict:

    """ Select the prompt template based on the position """

    if position == 'Data Analyst':
        PROMPT = PromptTemplate(
            template= prompts.da_template, input_variables=["context", "question"]
        )
        chain_type_kwargs = {"prompt": PROMPT}

    if position == 'Software Engineer':
        PROMPT = PromptTemplate(
            template= prompts.swe_template, input_variables=["context", "question"]
        )
        chain_type_kwargs = {"prompt": PROMPT}

    if position == 'Marketing':
        PROMPT = PromptTemplate(
            template= prompts.marketing_template, input_variables=["context", "question"]
        )
        chain_type_kwargs = {"prompt": PROMPT}

    return chain_type_kwargs

