import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def build_llm() -> ChatOpenAI:
    load_dotenv()

    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("请设置环境变量 DEEPSEEK_API_KEY（推荐）或 OPENAI_API_KEY")

    base_url = (
        os.getenv("DEEPSEEK_BASE_URL")
        or os.getenv("OPENAI_BASE_URL")
        or "https://api.deepseek.com/v1"
    )
    model = os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"

    return ChatOpenAI(model=model, api_key=api_key, base_url=base_url)


def main() -> None:
    llm = build_llm()
    result = llm.invoke("用一句话介绍一下你自己。")
    print(result.content)


if __name__ == "__main__":
    main()

