import openai
import json


def judge_answer(question, expected_answer, agent_answer, client, judge_guidance=None):
    """
    Use gpt-4o-mini to evaluate whether the agent's answer is correct.

    Args:
        question: The original question asked
        expected_answer: The ground truth answer
        agent_answer: The agent's response to evaluate
        client: An openai.OpenAI() client instance
        judge_guidance: Optional extra instructions for edge cases

    Returns:
        dict with 'verdict' ("PASS" or "FAIL") and 'reason' (brief explanation)
    """
    guidance_block = ""
    if judge_guidance:
        guidance_block = f"\nAdditional guidance for this question:\n{judge_guidance}\n"

    prompt = f"""You are an evaluation judge. Compare the agent's answer to the expected answer for correctness.

Rules:
- The agent does NOT need to match the expected answer word-for-word.
- PASS if the agent's answer contains the correct key facts, numbers, and names.
- FAIL if the agent provides incorrect numbers, wrong names, or missing critical information.
- Rounding to whole dollars is acceptable (e.g., "$446,306" instead of "$446,306.46") — PASS.
- If cents are included, they MUST be exact (e.g., "$446,306.48" instead of "$446,306.46") — FAIL.
- Extra correct information beyond the expected answer is acceptable — PASS.
- Omitting optional details is acceptable — PASS.
- Incorrect information of any kind is a FAIL.
{guidance_block}
Question: {question}

Expected Answer: {expected_answer}

Agent's Answer: {agent_answer}

Respond in JSON format only:
{{"verdict": "PASS" or "FAIL", "reason": "brief explanation"}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=200,
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a strict but fair evaluation judge. Respond only in JSON."},
                {"role": "user", "content": prompt}
            ]
        )

        result_text = response.choices[0].message.content.strip()

        # Parse JSON from response (handle markdown code blocks)
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        result = json.loads(result_text)
        return {
            "verdict": result.get("verdict", "FAIL"),
            "reason": result.get("reason", "No reason provided")
        }

    except Exception as e:
        return {
            "verdict": "ERROR",
            "reason": f"Judge error: {str(e)}"
        }
