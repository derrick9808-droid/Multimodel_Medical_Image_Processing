"""
Multi-Tier Normalization & Matching Engine.
Tier 1: Simple text cleanup (plain Python string methods: lowercase, strip punctuation, tokenization).
Tier 2: Synonym/alias canonical dictionary lookup.
Tier 3: Semantic similarity vector fallback (TF-IDF character/subword cosine similarity & word embeddings).
"""

import re
import string
from typing import List, Dict, Tuple, Any, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Extensive Canonical Synonym / Alias Lookup Table
CANONICAL_SYNONYMS: Dict[str, str] = {
    # Web & Roles
    "website developer": "web developer",
    "web dev": "web developer",
    "web development": "web developer",
    "frontend": "frontend developer",
    "frontend dev": "frontend developer",
    "front end developer": "frontend developer",
    "backend": "backend developer",
    "backend dev": "backend developer",
    "back end developer": "backend developer",
    "fullstack": "full stack developer",
    "full stack dev": "full stack developer",
    "fullstack engineer": "full stack developer",
    "software dev": "software engineer",
    "swe": "software engineer",
    "sre": "devops engineer",
    "site reliability engineer": "devops engineer",

    # Languages & Frameworks
    "py": "python",
    "python3": "python",
    "js": "javascript",
    "es6": "javascript",
    "ts": "typescript",
    "reactjs": "react",
    "react js": "react",
    "vuejs": "vue",
    "vue js": "vue",
    "nextjs": "next.js",
    "next js": "next.js",
    "nodejs": "node.js",
    "node js": "node.js",
    "expressjs": "express",
    "express js": "express",
    "golang": "go",
    "c plus plus": "c++",
    "cpp": "c++",
    "c sharp": "c#",
    "csharp": "c#",
    "ror": "ruby on rails",
    "rails": "ruby on rails",

    # AI / ML & Data
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "llm": "large language models",
    "genai": "generative ai",
    "tf": "tensorflow",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "shapley": "shap",

    # Cloud & DevOps
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "aws": "amazon web services",
    "gcp": "google cloud platform",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous deployment": "ci/cd",
    "continuous delivery": "ci/cd",
    "iac": "infrastructure as code",
    "tf cloud": "terraform",

    # Databases & Architecture
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "rest": "restful api",
    "rest api": "restful api",
    "rest apis": "restful api",
    "restful apis": "restful api",
    "micro services": "microservices",
    "microservice": "microservices"
}


def clean_text(text: str) -> str:
    """
    Tier 1 Cleanup:
    - Lowercase everything
    - Strip punctuation (preserving essential chars like + and # in c++ and c#)
    - Normalize whitespace
    """
    if not text:
        return ""
    cleaned = text.lower().strip()
    # Preserve '+' and '#' for c++ and c#
    punctuation_to_strip = string.punctuation.replace('+', '').replace('#', '').replace('.', '').replace('/', '')
    for char in punctuation_to_strip:
        cleaned = cleaned.replace(char, ' ')
    # Clean multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def tokenize_phrases(text: str) -> List[str]:
    """
    Tokenizes text into words and 2-3 word candidate skill phrases.
    """
    cleaned = clean_text(text)
    words = cleaned.split()
    tokens = list(words)
    # Generate bigrams and trigrams
    for i in range(len(words) - 1):
        tokens.append(f"{words[i]} {words[i+1]}")
    for i in range(len(words) - 2):
        tokens.append(f"{words[i]} {words[i+1]} {words[i+2]}")
    return tokens


def canonicalize_skill(skill_phrase: str) -> str:
    """
    Tier 2: Lookup in canonical synonym dictionary.
    """
    cleaned = clean_text(skill_phrase)
    # Direct dictionary check
    if cleaned in CANONICAL_SYNONYMS:
        return CANONICAL_SYNONYMS[cleaned]
    # Check without slash or dots
    alt = cleaned.replace('.', '').replace('/', ' ')
    if alt in CANONICAL_SYNONYMS:
        return CANONICAL_SYNONYMS[alt]
    return cleaned


def compute_semantic_similarity(phrase_a: str, phrase_b: str) -> float:
    """
    Tier 3 Fallback:
    Measures semantic similarity between two phrases using subword character n-gram TF-IDF vectorization.
    """
    ca = clean_text(phrase_a)
    cb = clean_text(phrase_b)
    if not ca or not cb:
        return 0.0
    if ca == cb:
        return 1.0

    try:
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        tfidf_matrix = vectorizer.fit_transform([ca, cb])
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(sim)
    except Exception:
        return 0.0


def match_skills(
    resume_skills: List[str],
    jd_skills: List[str],
    semantic_threshold: float = 0.70
) -> Dict[str, Any]:
    """
    Compares candidate resume skills against job description required skills.
    Runs Tier 1 normalization, Tier 2 canonical synonym lookup, and Tier 3 semantic similarity fallback.
    Returns matched skills, missing skills, extra candidate skills, and overlap ratio.
    """
    # Canonicalize all resume skills
    canonical_resume_map: Dict[str, str] = {} # canonical -> original
    for r_skill in resume_skills:
        canon = canonicalize_skill(r_skill)
        canonical_resume_map[canon] = r_skill

    matched: List[Dict[str, Any]] = []
    missing: List[str] = []

    for jd_skill in jd_skills:
        jd_canon = canonicalize_skill(jd_skill)
        # Check Tier 2 Canonical Match
        if jd_canon in canonical_resume_map:
            matched.append({
                "jd_skill": jd_skill,
                "resume_skill": canonical_resume_map[jd_canon],
                "canonical": jd_canon,
                "match_type": "Canonical / Exact Match",
                "similarity": 1.0
            })
            continue

        # Check Tier 3 Semantic Similarity Fallback
        best_sim = 0.0
        best_match = None
        for res_canon, orig_res_skill in canonical_resume_map.items():
            sim = compute_semantic_similarity(jd_canon, res_canon)
            if sim > best_sim:
                best_sim = sim
                best_match = orig_res_skill

        if best_sim >= semantic_threshold and best_match:
            matched.append({
                "jd_skill": jd_skill,
                "resume_skill": best_match,
                "canonical": jd_canon,
                "match_type": "Semantic Similarity Match",
                "similarity": round(best_sim, 2)
            })
        else:
            missing.append(jd_skill)

    # Candidate skills not required by JD
    matched_resume_originals = {m["resume_skill"].lower() for m in matched}
    extra_skills = [s for s in resume_skills if s.lower() not in matched_resume_originals]

    total_jd = len(jd_skills) if jd_skills else 1
    match_ratio = len(matched) / total_jd

    return {
        "matched": matched,
        "missing": missing,
        "extra_skills": extra_skills,
        "match_ratio": round(match_ratio, 3),
        "total_required": len(jd_skills),
        "total_matched": len(matched)
    }
