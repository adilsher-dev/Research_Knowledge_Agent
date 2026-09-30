from agent_workflow import research_graph, image_to_data_url

image_url = image_to_data_url(
    r"D:\RESEARCH_AGENT\Screenshot 2026-09-15 214414.png"
)

result = research_graph.invoke({
    "question": (
        "Analyze the race condition shown in this image, "
        "compare it with the programming and computer science "
        "technologies mentioned in my uploaded resume, "
        "and explain recent developments for preventing race conditions."
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

print("\nDOCUMENT RESULTS:")
print(len(result["document_results"]))

print("\nWEB RESULT:")
print(result["web_result"])

print("\nFINAL ANSWER:")
print(result["final_answer"])