# agents.py
# Defines the four specialized agents and wires them into a LangGraph workflow

import os
from typing import TypedDict, List
from openai import OpenAI
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from tools import web_search, format_search_results

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

MODEL = "openrouter/auto"


# ── SHARED STATE ──
# This is the object that flows through every node in the graph.
# Each agent reads from it and writes its own output back into it.
class AgentState(TypedDict):
    question: str
    raw_results: List[dict]
    research_text: str
    insights: str
    report: str
    activity_log: List[str]


def call_llm(system_prompt: str, user_prompt: str) -> str:
    # Shared helper — every agent uses this to talk to the LLM
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content


# ── NODE 1: RESEARCHER ──
def researcher_node(state: AgentState) -> AgentState:
    state["activity_log"].append("Researcher Agent: searching the web...")

    results = web_search(state["question"], max_results=5)
    formatted = format_search_results(results)

    state["raw_results"] = results
    state["research_text"] = formatted
    state["activity_log"].append(f"Researcher Agent: found {len(results)} sources.")
    return state


# ── NODE 2: ANALYST ──
def analyst_node(state: AgentState) -> AgentState:
    state["activity_log"].append("Analyst Agent: extracting key insights...")

    system_prompt = (
        "You are an Analyst Agent. Your only job is to read research findings "
        "and extract the most important, relevant insights related to the user's question. "
        "Be concise. Output a clear bullet list of insights. Do not write a full report."
    )
    user_prompt = f"Question: {state['question']}\n\nResearch findings:\n{state['research_text']}"

    state["insights"] = call_llm(system_prompt, user_prompt)
    state["activity_log"].append("Analyst Agent: insights extracted.")
    return state


# ── NODE 3: WRITER ──
def writer_node(state: AgentState) -> AgentState:
    state["activity_log"].append("Writer Agent: drafting final report...")

    system_prompt = (
        "You are a Writer Agent. Your only job is to take analytical insights "
        "and write a clear, well-structured final report answering the user's question. "
        "Use short paragraphs and headers where useful. Be professional and objective."
    )
    user_prompt = f"Question: {state['question']}\n\nKey insights:\n{state['insights']}"

    state["report"] = call_llm(system_prompt, user_prompt)
    state["activity_log"].append("Writer Agent: report complete.")
    return state


# ── BUILD THE GRAPH ──
def build_graph():
    graph = StateGraph(AgentState)

    # Register each agent as a node
    graph.add_node("researcher", researcher_node)
    graph.add_node("analyst", analyst_node)
    graph.add_node("writer", writer_node)

    # Wire them in order: researcher -> analyst -> writer -> END
    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


# ── PUBLIC FUNCTION main.py WILL CALL ──
def run_research_pipeline(question: str) -> dict:
    app = build_graph()

    initial_state: AgentState = {
        "question": question,
        "raw_results": [],
        "research_text": "",
        "insights": "",
        "report": "",
        "activity_log": []
    }

    final_state = app.invoke(initial_state)
    return final_state