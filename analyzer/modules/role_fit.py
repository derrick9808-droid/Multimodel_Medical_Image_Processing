"""
Role-Fit Heatmap & Radar Comparison Engine.
Evaluates a single candidate resume across multiple industry benchmark profiles
(Backend, Frontend, Full-Stack, DevOps, Data Science/ML, Mobile, Technical Lead)
generating radar/spider chart datasets and fit percentages.
"""

from typing import List, Dict, Any
from .matcher import match_skills

BENCHMARK_ROLES: Dict[str, Dict[str, Any]] = {
    "Backend Engineer": {
        "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "REST APIs", "Microservices", "Docker", "SQL", "gRPC"],
        "color": "rgba(99, 102, 241, 0.8)", # Indigo
        "category": "Core Engineering"
    },
    "Frontend Engineer": {
        "skills": ["JavaScript", "TypeScript", "React", "Next.js", "HTML5", "CSS3", "Tailwind CSS", "Redux", "GraphQL"],
        "color": "rgba(14, 165, 233, 0.8)", # Sky blue
        "category": "UI / Client"
    },
    "Full-Stack Engineer": {
        "skills": ["Python", "JavaScript", "TypeScript", "Django", "React", "PostgreSQL", "REST APIs", "Docker", "Git"],
        "color": "rgba(16, 185, 129, 0.8)", # Emerald
        "category": "Cross-Functional"
    },
    "DevOps & SRE": {
        "skills": ["Kubernetes", "Docker", "AWS", "Terraform", "CI/CD", "Linux", "Bash", "Jenkins", "Nginx", "Monitoring"],
        "color": "rgba(245, 158, 11, 0.8)", # Amber
        "category": "Infrastructure"
    },
    "Data & ML Engineer": {
        "skills": ["Python", "Machine Learning", "PyTorch", "TensorFlow", "scikit-learn", "Pandas", "NumPy", "SQL", "NLP", "SHAP"],
        "color": "rgba(168, 85, 247, 0.8)", # Purple
        "category": "AI / Analytics"
    },
    "Mobile Developer": {
        "skills": ["Swift", "Kotlin", "React Native", "Flutter", "iOS", "Android", "Mobile Architecture", "REST APIs"],
        "color": "rgba(244, 63, 94, 0.8)", # Rose
        "category": "Mobile"
    },
    "Engineering Lead": {
        "skills": ["System Design", "Agile", "Mentorship", "Microservices", "Code Review", "Cloud Architecture", "Leadership"],
        "color": "rgba(20, 184, 166, 0.8)", # Teal
        "category": "Management"
    }
}


def calculate_role_fit_matrix(candidate_skills: List[str]) -> Dict[str, Any]:
    """
    Computes fit score (0-100%) against each benchmark role profile.
    Returns Chart.js compatible radar chart datasets and detailed breakdown.
    """
    role_results: List[Dict[str, Any]] = []
    labels: List[str] = []
    scores: List[float] = []

    for role_name, profile in BENCHMARK_ROLES.items():
        role_skills = profile["skills"]
        match_res = match_skills(candidate_skills, role_skills)
        match_ratio = match_res["match_ratio"]

        # Calculate weighted score (boosted slightly if extra related skills exist)
        matched_count = match_res["total_matched"]
        total_req = match_res["total_required"]
        raw_score = (matched_count / total_req) * 100
        score = min(100.0, round(raw_score, 1))

        labels.append(role_name)
        scores.append(score)

        role_results.append({
            "role_name": role_name,
            "category": profile["category"],
            "score": score,
            "matched_skills": [m["canonical"].title() for m in match_res["matched"]],
            "missing_skills": match_res["missing"],
            "color": profile["color"]
        })

    # Sort descending by score to identify primary and secondary strengths
    ranked_roles = sorted(role_results, key=lambda x: x["score"], reverse=True)
    best_role = ranked_roles[0]["role_name"] if ranked_roles else "Generalist"

    return {
        "radar_data": {
            "labels": labels,
            "scores": scores
        },
        "ranked_roles": ranked_roles,
        "best_fit_role": best_role,
        "average_fit_score": round(sum(scores) / len(scores), 1) if scores else 0.0
    }
