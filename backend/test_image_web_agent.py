from agent_workflow import research_graph, image_to_data_url

image_url = image_to_data_url(
    r"D:\RESEARCH_AGENT\Screenshot 2026-09-15 214414.png"
)

result = research_graph.invoke({
    "question": (
        "Analyze the race condition shown in this image "
        "and explain recent developments in handling race conditions "
        "in modern programming systems."
    ),
    "route": "",
    "plan_reason": "",
    "image_data_url": image_url,
    "image_result": "",
    "document_results": [],
    "web_result": "",
    "final_answer": "",
    "user_id": 1  # id of a registered user in the users table
})

print("\nROUTE:")
print(result["route"])

print("\nPLAN REASON:")
print(result["plan_reason"])

print("\nIMAGE RESULT:")
print(result["image_result"])

print("\nWEB RESULT:")
print(result["web_result"])

print("\nFINAL ANSWER:")
print(result["final_answer"])