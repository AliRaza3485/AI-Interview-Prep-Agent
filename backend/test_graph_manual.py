from graph.state import get_initial_state
from graph.interview_graph import app_graph

# Yeh schema resume_parser.py ke structure_resume() output se match karta hai
resume_data = {
    "skills": ["Python", "FastAPI", "SQL", "Git"],
    "experience": [
        {
            "title": "Backend Developer",
            "company": "XYZ Solutions",
            "duration": "2022 - Present",
            "highlights": [
                "Built REST APIs using FastAPI",
                "Worked with PostgreSQL databases",
            ],
        }
    ],
    "projects": [
        {
            "name": "Inventory Management API",
            "description": "A REST API to track warehouse inventory",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        }
    ],
    "education": [
        {
            "degree": "BS Computer Science",
            "institution": "Some University",
            "year": "2022",
        }
    ],
}

# Yeh schema jd_parser.py ke structure_jd() output se match karta hai
jd_data = {
    "role_title": "Backend Engineer",
    "role_level": "Mid",
    "required_skills": ["Python", "FastAPI", "Docker", "Kubernetes"],
    "nice_to_have_skills": ["AWS"],
    "responsibilities": [
        "Design and maintain backend services",
        "Deploy and monitor containerized applications",
    ],
    "keywords": ["microservices", "REST API", "containerization"],
}

initial_state = get_initial_state(resume_data, jd_data)
final_state = app_graph.invoke(initial_state)

print("=== GAP ANALYSIS ===")
print(final_state["gap_analysis"])
print()
print("=== QUESTIONS ===")
for q in final_state["questions"]:
    print(q)
