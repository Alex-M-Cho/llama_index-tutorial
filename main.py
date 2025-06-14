from llama_index.llms.ollama import Ollama
from llama_parse import LlamaParse
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, PromptTemplate
from llama_index.core.embeddings import resolve_embed_model
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.agent import ReActAgent
from pydantic import BaseModel
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core.query_pipeline import QueryPipeline
from code_reader import code_reader
from prompts import context, code_parser_template
import ast
import os
from dotenv import load_dotenv



load_dotenv()

llm = Ollama(model="mistral", request_timeout=30)

parser = LlamaParse(result_type="markdown")

file_extractor = {".pdf": parser}

documents = SimpleDirectoryReader("./data", file_extractor=file_extractor).load_data()

embed_model = resolve_embed_model("local:BAAI/bge-m3")

vector_index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)

query_engine = vector_index.as_query_engine(llm=llm)


tools = [
    QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="api_documentdation",
            description="this gives documentation about code for an API. Use this for reading docs for the API"
        )
    ),
    code_reader,
]

code_llm = Ollama(model="codellama")

agent = ReActAgent.from_tools(tools, llm=code_llm, verbose=True, context=context)

class CodeOutput(BaseModel):
    code: str
    description: str
    filename: str

parser = PydanticOutputParser(CodeOutput)

json_prompt_str = parser.format(code_parser_template)

json_prompt_template = PromptTemplate(json_prompt_str)

output_pipleline = QueryPipeline(chain=[json_prompt_template, code_llm])

while (prompt := input("Enter a prompt (q to quit): ")) !="q":

    retires = 0
    while retires < 3:
        try:
            result = agent.query(prompt)
            next_result = output_pipleline.run(response=result)
            cleaned_json = ast.literal_eval(str(next_result).replace("assistant:", ""))
            break
        except Exception as e:
            retires += 1
            print(f"Error occured, retry #{retires}: {e}")

    if retires >= 3:
        print("Failed to generate code after 3 retries. Please try again.")
        continue

    print("Code generated successfully")
    print(cleaned_json["code"])

    print("\n\n Description:", cleaned_json["description"])

    filename = cleaned_json["filename"]

    try:
        with open(os.path.join("output", filename), "w") as f:
            f.write(cleaned_json["code"])
        print(f"Saved file successfully {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")
    



