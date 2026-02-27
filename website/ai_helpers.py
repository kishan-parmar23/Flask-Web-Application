import json
import os
from typing import Any, Dict, List, Optional

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    requests = None


def _contains_any(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def analyze_error_message(message: str, extra_fields: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Analyze an error report for common quality heuristics and return a
    structured result that templates can render.
    """
    text = (message or "").strip()
    extra_fields = extra_fields or {}

    checks: List[Dict[str, Any]] = []

    # Summary / title
    summary_text = extra_fields.get("summary", "")
    summary_source = summary_text or text
    has_summary = len(summary_source.split()) >= 6
    checks.append(
        {
            "name": "Summary",
            "ok": has_summary,
            "detail": (
                "Clear high-level summary present."
                if has_summary
                else "Add a short 1–2 sentence summary of the problem."
            ),
        }
    )

    # Steps to reproduce
    steps_text = extra_fields.get("steps", "") or text
    has_steps = _contains_any(
        steps_text,
        [
            "steps to reproduce",
            "step 1",
            "step 2",
            "1.",
            "2.",
            "click",
            "then",
        ],
    )
    checks.append(
        {
            "name": "Steps to reproduce",
            "ok": has_steps,
            "detail": (
                "Specific steps to reproduce are described."
                if has_steps
                else "List the exact steps someone can follow to trigger the issue."
            ),
        }
    )

    # Expected vs actual behaviour
    expected_text = extra_fields.get("expected", "") or text
    actual_text = extra_fields.get("actual", "") or text
    has_expected = _contains_any(
        expected_text,
        ["expected", "should", "supposed to", "i thought", "i expect"],
    )
    has_actual = _contains_any(
        actual_text,
        ["actually", "instead", "but it", "what happens", "got", "seen"],
    )
    has_expected_actual = has_expected and has_actual
    checks.append(
        {
            "name": "Expected vs actual behaviour",
            "ok": has_expected_actual,
            "detail": (
                "Both expected and actual behaviour are clearly described."
                if has_expected_actual
                else "State what you expected to happen and what actually happened."
            ),
        }
    )

    # Environment / context
    env_text = extra_fields.get("environment", "") or text
    has_environment = _contains_any(
        env_text,
        [
            "windows",
            "macos",
            "linux",
            "ubuntu",
            "chrome",
            "firefox",
            "safari",
            "edge",
            "version",
            "python",
            "flask",
            "os",
        ],
    )
    checks.append(
        {
            "name": "Environment details",
            "ok": has_environment,
            "detail": (
                "Environment (OS, versions, browser, etc.) is included."
                if has_environment
                else "Mention your OS, browser or app version, and any relevant environment details."
            ),
        }
    )

    # Error text / stack trace
    has_stack_trace = _contains_any(
        text,
        [
            "traceback",
            "error:",
            "exception",
            "stack trace",
            "typeerror",
            "valueerror",
            "keyerror",
        ],
    ) or "\n" in text
    checks.append(
        {
            "name": "Error text or stack trace",
            "ok": has_stack_trace,
            "detail": (
                "Error message or stack trace is included."
                if has_stack_trace
                else "Include the exact error message or stack trace (with sensitive data removed)."
            ),
        }
    )

    total = len(checks)
    passed = sum(1 for c in checks if c["ok"])
    score = int(round((passed / total) * 100)) if total else 0

    return {
        "score": score,
        "checks": checks,
    }


def call_ai_feedback_api(message: str, analysis: Dict[str, Any]) -> str:
    """
    Call an external AI provider to get natural-language feedback on how to
    improve the error report. Falls back gracefully if configuration is
    missing or the request fails.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if not api_key or requests is None:
        return (
            "AI feedback is currently unavailable. "
            "You can still use the checklist above to improve your message."
        )

    system_prompt = (
        "You help users write clearer, more actionable bug reports. "
        "Given their current report and an analysis of which parts are missing, "
        "suggest specific improvements in plain language."
    )

    user_payload = {
        "message": message,
        "analysis": analysis,
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    "Here is the current error/bug report and a structured analysis "
                    "of it. Suggest concrete ways to improve it so that another "
                    "developer could easily reproduce and fix the issue.\n\n"
                    f"Report:\n{message}\n\n"
                    f"Analysis:\n{json.dumps(user_payload, indent=2)}"
                ),
            },
        ],
        "temperature": 0.2,
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise ValueError("No choices in AI response.")
        message_content = choices[0].get("message", {}).get("content")
        if not message_content:
            raise ValueError("Empty AI response content.")
        return str(message_content).strip()
    except Exception:
        return (
            "AI feedback could not be retrieved right now due to an error "
            "contacting the AI service. Please refine your report using the "
            "checklist above and try again later."
        )

