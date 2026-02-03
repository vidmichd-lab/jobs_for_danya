"""
Generate cover letters using Yandex GPT (Yandex Cloud LLM API).
"""
import os
import requests
from config import (
    PROFILE_PATH,
    INSTRUCTION_PATH,
    YANDEX_API_KEY,
    YANDEX_IAM_TOKEN,
    YANDEX_FOLDER_ID,
    YANDEX_MODEL_URI,
)

COMPLETION_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"


def _load_text(path) -> str:
    if path and path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def _auth_header() -> dict:
    if YANDEX_IAM_TOKEN:
        return {"Authorization": f"Bearer {YANDEX_IAM_TOKEN}"}
    if YANDEX_API_KEY:
        return {"Authorization": f"Api-Key {YANDEX_API_KEY}"}
    return {}


def generate_cover_letter(
    job_title: str,
    job_description: str,
    company: str = "",
) -> str:
    """
    Call Yandex GPT with instruction + profile + job details; return cover letter text.
    """
    instruction = _load_text(INSTRUCTION_PATH)
    profile = _load_text(PROFILE_PATH)
    user_content = f"""Candidate profile (use only this for facts):

{profile}

---

Job to apply for:
- Title: {job_title}
- Company: {company or "Company"}
- Description (excerpt): {job_description[:3000]}

Write a short cover letter for this job in English. Output only the letter text."""

    # Yandex completion API: folderId, modelUri, completionOptions, messages
    model_uri = YANDEX_MODEL_URI or f"gpt://{YANDEX_FOLDER_ID}/aliceai-llm/latest"
    payload = {
        "folderId": YANDEX_FOLDER_ID,
        "modelUri": model_uri,
        "completionOptions": {
            "temperature": 0.4,
            "maxTokens": 1024,
        },
        "messages": [
            {"role": "system", "text": instruction},
            {"role": "user", "text": user_content},
        ],
    }
    headers = {
        "Content-Type": "application/json",
        **_auth_header(),
    }
    r = requests.post(COMPLETION_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()
    # Response shape: result.alternatives[0].message.text
    result = data.get("result") or {}
    alternatives = result.get("alternatives") or []
    if not alternatives:
        return ""
    return (alternatives[0].get("message") or {}).get("text", "").strip()


if __name__ == "__main__":
    # Quick test
    profile = _load_text(PROFILE_PATH)
    instruction = _load_text(INSTRUCTION_PATH)
    print("Profile length:", len(profile))
    print("Instruction length:", len(instruction))
    if not (YANDEX_API_KEY or YANDEX_IAM_TOKEN):
        print("Set YANDEX_API_KEY or YANDEX_IAM_TOKEN to test generation.")
