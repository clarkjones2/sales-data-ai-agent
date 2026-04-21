import matplotlib.pyplot as plt

models = [
    "Claude sonnet-4-20250514",
    "OpenAI gpt-5-mini",
    "OpenAI gpt-4o",
    "OpenAI gpt-4o-mini",
    "OpenAI gpt-5-nano",
    "OpenAI gpt-4.1"
]
costs = [0.45, 0.03, 0.16, 0.01, 0.02, 0.12]

plt.figure(figsize=(10, 5))
plt.bar(models, costs, color='skyblue')
plt.ylabel("Cost ($)")
plt.title("Model Cost Comparison")
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.show()
