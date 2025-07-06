from openai import AsyncOpenAI
from dotenv import load_dotenv
import base64
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import MarkdownHeaderTextSplitter
import re
import requests
import textwrap
import openai
from langchain.docstore.document import Document

# Загрузка переменных окружения
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# функция для загрузки документа по ссылке из гугл драйв
def load_document_text_from_google_drive(url: str) -> str:
    # Extract the document ID from the URL
    match_ = re.search('/document/d/([a-zA-Z0-9-_]+)', url)
    if match_ is None:
        raise ValueError('Invalid Google Docs URL')
    doc_id = match_.group(1)
    # Download the document as plain text
    response = requests.get(f'https://docs.google.com/document/d/{doc_id}/export?format=txt')
    response.raise_for_status()
    text = response.text
    return text

def load_document_text(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text
    except Exception as e:
        raise ValueError(f"Ошибка при чтении текстового файла: {e}")

# Преобразование текстав формат MarkDown с заголовками под #
# Функция полезна, если вы решите формировать чанки через MarkdownHeaderTextSplitter
def text_to_markdown(text):
    # Добавляем заголовок 1 уровня на основе римских чисел (без переноса строки)
    def replace_header1(match):
        return f"# {match.group(2)}\n{match.group(2)}"
    text = re.sub(r'^(I{1,3}|IV|V)\. (.+)', replace_header1, text, flags=re.M)
    # Добавляем текст, выделенный жирным шрифтом (он заключен между *)
    # и дублируем его строчкой ниже
    def replace_header2(match):
        return f"## {match.group(1)}\n{match.group(1)}"
    text = re.sub(r'\*([^\*]+)\*', replace_header2, text)
    return text

# База знаний
#data_from_url = load_document_text('https://docs.google.com/document/d/19ULhntll5HNDKiLIwzvyCSlB2KsgxnILGsYh8DWN39s/edit?usp=sharing')

data_from_url = load_document_text('igorvolnukhinai_kb.txt');
# Предобрабатываем текст в формат маркдаун разметки
markdown = text_to_markdown(data_from_url)

# делим БЗ на чанки при помощи MarkdownHeaderTextSplitter, так как предварительно мы ее разметили именно таким образом
headers_to_split_on = [
        ("###", "Header 1"),
        ("##", "Header 2"),
	("#", "Header 3")]

markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
fragments = markdown_splitter.split_text(markdown)

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Преобразуем чанки в объекты Document
documents = [Document(page_content=fragment.page_content, metadata=fragment.metadata) for fragment in fragments]

# Создаём векторное хранилище
embeddings = OpenAIEmbeddings()
db = FAISS.from_documents(documents, embeddings)
retriever = db.as_retriever()

# Инструкция для нейро-консультанта
system_instruction = (
    "Ты — цифровой двойник Игоря Волнухина. Твоя задача — представлять его профессионально в переписке и на собеседовании с рекрутером."
    "У тебя есть доступ к полной базе знаний о нём: опыт, достижения, проекты, курсы, навыки, ценности, карьерные цели, формат работы, ожидания по зарплате и волонтёрская деятельность. Используй только эти данные — не придумывай ничего от себя."
    "Ты разговариваешь от **первого лица**, как будто ты и есть Игорь. Общайся профессионально, уверенно и вежливо. Не пиши, что ты — ИИ."
    "Основные правила:"
    "– Отвечай **на том языке, на котором задан вопрос** (русский, английский и т.д.);"
    "– Если вопрос не входит в сферу знаний — скажи, что уточнишь позже по почте;"
    "– Если тебя просят конкретные примеры — используй реальные кейсы из проектов;"
    "– Отвечай коротко, но содержательно, избегай воды."
    " Используй заранее известные параметры:"
    "– Ожидаемая зарплата: 2 500 000 тенге в месяц или 14 000 тенге в час;"
    "– Форматы сотрудничества: full-time, part-time, удалённо, офис в Астане, релокация в Дубай, временные проекты, работа в штате;"
    "– Основные компетенции: Project Management (PMBoK, Scrum, SAFe, ITIL), внедрение ИТ-решений, системная интеграция, управление командами и подрядчиками, аналитика и автоматизация бизнес-процессов."
    "Ты проходишь собеседование — отвечай как опытный, уверенный и ценный кандидат."
)

# Шаблон запроса
prompt_template = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        f"System: {system_instruction}\n\n"
        "Context:\n{context}\n\n"
        "Вопрос: {question}\nОтвет:"
    )
)

# Создаём LLM-модель и Retrieval QA-цепочку
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": prompt_template}
)

async def answer_gpt(question: str):
    try:
        result = await qa_chain.ainvoke({"query": question})
        return {"answer": result}
    except Exception as e:
        print(f"answer_gpt() error: {e}")
        return {"answer": "Ошибка при обращении к OpenAI"}
