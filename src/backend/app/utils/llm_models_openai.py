from openai import OpenAI
import json

class OpenAIModel:
    def __init__(self, api_key : str):
        self.client = OpenAI(api_key=api_key)

    def get_tldr(self, user_query: str, article_text: str):
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            stop=["```"],
            temperature=0.5,
            max_tokens=4096,
            top_p=0.2,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
                "type": "text"
            },
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a helpful assistant. Your task is to generate a TLDR relative to the user's query. "
                        "The response should be in JSON format with a single property called 'tldr'. "
                        "The 'tldr' should be a concise summary of the article, tailored to answer how the article is relevant to the user's query. "
                        "The response should be in Portuguese."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "{\n"
                        "  \"user_query\": \"Qual é o impacto do desmatamento na biodiversidade?\",\n"
                        "  \"article_text\": \"O desmatamento é a principal causa de perda de biodiversidade, afetando diretamente os habitats das espécies, resultando na extinção de várias delas. Além disso, o desmatamento provoca desequilíbrios nos ecossistemas, reduzindo a capacidade da natureza de se regenerar.\"\n"
                        "}\n```json"
                    )
                },
                {
                    "role": "assistant",
                    "content": (
                        "{\n"
                        "  \"tldr\": \"O desmatamento leva à perda de biodiversidade ao destruir habitats, o que pode causar a extinção de várias espécies e desequilíbrios nos ecossistemas.\"\n"
                        "}\n```"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "{\n"
                        f"  \"user_query\": \"{user_query}\",\n"
                        f"  \"article_text\": \"{article_text}\"\n"
                        "}\n```json"
                    )
                }
            ]
        )
        # Extract and load the result as JSON
        result_json = json.loads(completion.choices[0].message.content)
        return result_json['tldr']

        