from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

output_parser = StrOutputParser()

question_rewrite_template = PromptTemplate(
    template="""
You are an AI assistant that rewrites user questions to be clearer and more specific, 
while staying neutral and focused.

Original question:
{question}

Rewritten question:
""",
    input_variables=["question"]
)


final_answer_template = PromptTemplate(
    template="""
You are a helpful assistant analyzing a GitHub repository.
Answer the question based ONLY on context provided below.

If answer is not present in the context — say "I don't know".

Context:
{context}

Question:
{question}

Answer:
""",
    input_variables=["context", "question"]
)
