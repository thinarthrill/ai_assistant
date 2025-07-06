# fastapi[all]
from fastapi import FastAPI, HTTPException, Request, Depends, File, Form, UploadFile
from functions import answer_gpt
from qazpmichapterfunctions import answer_qazpmichaptergpt
from typing import Dict
from urllib.parse import urlencode
import asyncio
import hmac
import hashlib
import os
from fastapi.middleware.cors import CORSMiddleware

llm = FastAPI(title="LLM_API")
UPLOAD_DIR = "/temp/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# клиенты / токены для авторизации
AUTHORIZED_TOKENS = {"client_1": "F3VU4rFXzt7Rp", }


llm.add_middleware(
    CORSMiddleware,          # позволяет веб-страницам делать запросы к ресурсам, расположенным на другом домене
    allow_origins=["https://projectsolution.kz", "https://pmi.org.kz"],     # Разрешить доступ из любого источника (все домены)
    allow_credentials=True,  # Разрешить отправку cookies и других учетных данных
    allow_methods=["*"],     # Разрешить все HTTP-методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],     # Разрешить все заголовки в запросах
)


# Функция создает цифровую подпись для переданных параметров с использованием
# ключа token и алгоритма хеширования SHA256
def gen_signature(token: str, params: dict) -> str:
    return hmac.new(token.encode('utf-8'),
                    urlencode(params).encode('utf-8'),
                    hashlib.sha256).hexdigest()


# Функция для проверки подписи
def verify_signature(signature: str, params: dict, secret_token: str) -> bool:
    expected_signature = gen_signature(secret_token, params)
    return hmac.compare_digest(expected_signature, signature)


# Проверка подписи (при отправке json)
async def verify_token(request: Request):
    try:
        # Проверяем, что тело запроса корректно
        body = await request.json()
        # Извлекаем `client_id` и `signature`
        client_id = body.get("client_id")
        signature = body.get("signature")
        # Подготовка данных для подписи без "signature"
        body_without_signature = {
            k: v for k, v in body.items() if k not in ("signature")}
        # Получаем токен для указанного `client_id`
        secret_token = AUTHORIZED_TOKENS[client_id]
        # Проверка подписи
        if not verify_signature(signature, body_without_signature, secret_token):
            raise HTTPException(status_code=401, detail="Invalid signature")
        return True  # Авторизация успешна
    except Exception as e:
        print(f"Error in verify_token: {str(e)}")
        raise HTTPException(
            status_code=400, detail="Invalid request format")


@llm.post("/upload_file")
async def upload_file(file: UploadFile = File(...),
                      client_id: str = Form(...),
                      signature: str = Form(...)):
    try:
        body = {"client_id": client_id}  # Подготовка данных для подписи
        secret_token = AUTHORIZED_TOKENS[client_id]
        if not verify_signature(signature, body, secret_token):
            raise HTTPException(status_code=401, detail="Invalid signature")
        # Сохранение файла
        file_name = os.path.basename(file.filename)
        file_location = os.path.join(UPLOAD_DIR, file_name)
        with open(file_location, "wb") as f:
            f.write(await file.read())
        return {"upload_file_path": file_location}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"File upload failed: {str(e)}")


@llm.post("/openai")
async def post_answer_gpt(query: Dict,
                          valid: bool = Depends(verify_token)):
    try:
        result = await answer_gpt(query["query"])
        return {"answer": result}
    except Exception as ex:
        print(f'post_answer_gpt() error: {ex}')
        return {"answer": "Ошибка при обработке запроса."}

@llm.post("/openai_image")
async def post_image_recognition(query: Dict,
                                 valid: bool = Depends(verify_token)):
    try:
        result = await image_recognition(query["image_path"])
        await asyncio.to_thread(os.remove, query["image_path"])
        return result
    except Exception as ex:
        print(f'post_image_recognition() error: {ex}')


@llm.post("/openai_whisper")
async def post_stt_whisper(query: Dict,
                           valid: bool = Depends(verify_token)):
    try:
        answer = await stt_whisper_online(query["voice_file"])
        await asyncio.to_thread(os.remove, query["voice_file"])
        return answer
    except Exception as ex:
        return f'post_stt_whisper(): \n{ex}'

@llm.post("/qazpmichapter")
async def post_answer_qazpmichaptergpt(query: Dict,
                          valid: bool = Depends(verify_token)):
    try:
        result = await answer_qazpmichaptergpt(query["query"])
        return {"answer": result}
    except Exception as ex:
        print(f'post_answer_qazpmichaptergpt() error: {ex}')
        return {"answer": "Ошибка при обработке запроса."}

# Если запускать локально в терминале:
# cd (перейти в папку с api_llm.py)
# uvicorn api_llm:llm --reload
