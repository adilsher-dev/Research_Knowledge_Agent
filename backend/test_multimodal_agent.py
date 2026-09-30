from agent_workflow import research_graph, image_to_data_url

image_url = image_to_data_url(
    r"D:\RESEARCH_AGENT\Screenshot 2026-09-15 214414.png"
)

result = research_graph.invoke({
    "question": "Compare the code shown in this image with the programming technologies mentioned in my uploaded resume.",
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

print("\nFINAL ANSWER:")
print(result["final_answer"])