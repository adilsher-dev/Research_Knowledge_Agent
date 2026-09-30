from agent_workflow import research_graph


result = research_graph.invoke(
    {
        "question": "Based on my RAG project in my resume, what recent RAG techniques could I add to improve it?",
        "route": "",
        "plan_reason": "",
        "document_results": [],
        "web_result": "",
        "final_answer": "",
        "user_id": 1  # id of a registered user in the users table
    }
)

print("\nFINAL RESULT:")
print(result)