import os

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")

app = Flask(__name__)
client = anthropic.Anthropic(api_key=API_KEY) if API_KEY else None

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

# Демо-данные вымышленного интернет-магазина — ассистент отвечает только
# опираясь на эти правила, не выдумывая ничего от себя.
SYSTEM_PROMPT = """
Ты — ассистент поддержки интернет-магазина электроники "TechStore".
Отвечай кратко, дружелюбно, только на русском языке.
Пиши обычным текстом без markdown-разметки — никаких **, *, #, - для списков
и т.п. Если нужно перечислить пункты, используй просто "1)", "2)" или новую строку.
Используй только информацию из правил магазина ниже. Если вопрос не
касается магазина или ответа нет в правилах — вежливо скажи, что не
можешь ответить, и предложи написать в поддержку на support@techstore.example.

Правила магазина TechStore:
- Доставка по России: 3-5 рабочих дней, бесплатно при заказе от 3000 руб.
- Возврат товара: в течение 14 дней с момента получения, товар должен быть
  в оригинальной упаковке и не иметь следов использования.
- Гарантия: 12 месяцев на всю технику, гарантийный ремонт — бесплатно.
- Оплата: картой онлайн или наличными при получении.
- Отследить заказ можно в личном кабинете на сайте по номеру заказа.
"""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    if client is None:
        return jsonify({"error": "Не настроен ANTHROPIC_API_KEY на сервере."}), 500

    data = request.get_json(force=True)
    history = data.get("history", [])

    if not history:
        return jsonify({"error": "Пустой запрос."}), 400

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=history,
        )
    except anthropic.APIError as e:
        return jsonify(
            {"error": f"Ошибка обращения к Claude API: {e}. Проверь ANTHROPIC_API_KEY в .env."}
        ), 502
    except Exception as e:
        return jsonify({"error": f"Не удалось получить ответ: {e}"}), 500

    text_blocks = [block.text for block in response.content if block.type == "text"]
    reply_text = "\n".join(text_blocks) if text_blocks else "(пустой ответ)"

    return jsonify({"reply": reply_text})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
