from langgraph.graph import StateGraph, END

from graph.state import InterviewState
from agents.analyzer_agent import analyze_gap
from agents.question_generator_agent import generate_questions
from config import settings
from parsers.llm_client import GroqLLMClient

# Shared LLM client jo dono nodes use karenge
llm_client = GroqLLMClient(api_key=settings.GROQ_API_KEY)


def analyze_node(state: InterviewState) -> InterviewState:
    """
    State se resume_data aur jd_data uthata hai, analyze_gap() call karta hai,
    aur result ko state ke gap_analysis field mein daal deta hai.
    """
    gap_analysis = analyze_gap(
        resume_data=state["resume_data"],
        jd_data=state["jd_data"],
        llm_client=llm_client,
        model=settings.GROQ_MODEL,
    )
    state["gap_analysis"] = gap_analysis
    return state


def generate_questions_node(state: InterviewState) -> InterviewState:
    """
    State se gap_analysis, resume_data, jd_data uthata hai, generate_questions() call
    karta hai, aur result ko state ke questions field mein daal deta hai.
    """
    questions = generate_questions(
        gap_analysis=state["gap_analysis"],
        resume_data=state["resume_data"],
        jd_data=state["jd_data"],
        llm_client=llm_client,
        model=settings.GROQ_MODEL,
    )
    state["questions"] = questions
    return state


def build_graph():
    """
    Graph banata hai aur compile kar ke return karta hai.
    Abhi sirf 2 nodes hain: analyze -> generate_questions -> end
    Day 3+ mein interview_loop, evaluate, report nodes yahan add honge.
    """
    graph = StateGraph(InterviewState)

    graph.add_node("analyze", analyze_node)
    graph.add_node("generate_questions", generate_questions_node)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "generate_questions")
    graph.add_edge("generate_questions", END)

    return graph.compile()


# Module-level compiled graph, taake API routes ya scripts seedha import kar sakein
app_graph = build_graph()
