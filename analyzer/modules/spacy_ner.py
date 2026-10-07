"""
Custom Named Entity Recognition (NER) module using spaCy.
Recognizes SKILL, DEGREE, EXPERIENCE, and DATE entities from resume text.
Includes training dataset and automatic model compilation/persistence.
"""

import os
import re
import spacy
from pathlib import Path
from typing import Dict, List, Any
from spacy.tokens import DocBin
from spacy.training import Example
from spacy.pipeline import EntityRuler

MODEL_DIR = Path(__file__).resolve().parent.parent / "custom_ner_model"

# Entity patterns for rule-based bootstrapping & high precision matching
SKILL_PATTERNS = [
    # Programming & Frameworks
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Golang", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin",
    "Django", "Flask", "FastAPI", "React", "React.js", "Next.js", "Vue", "Vue.js", "Angular", "Node.js", "Express", "Spring Boot",
    "HTML5", "CSS3", "Tailwind CSS", "Bootstrap", "GraphQL", "REST APIs", "RESTful API", "gRPC", "Microservices",
    # Databases & Storage
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Cassandra", "Elasticsearch", "DynamoDB", "Oracle",
    # Cloud & DevOps
    "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "K8s", "Terraform", "CI/CD",
    "Jenkins", "GitHub Actions", "GitLab CI", "Linux", "Bash", "Nginx", "Apache", "Ansible",
    # AI / ML & Data Science
    "Machine Learning", "Deep Learning", "NLP", "Natural Language Processing", "Computer Vision",
    "PyTorch", "TensorFlow", "Keras", "scikit-learn", "Pandas", "NumPy", "spaCy", "NLTK", "Hugging Face", "LLM", "SHAP",
    "Data Analysis", "SQL", "Tableau", "Power BI", "Apache Spark", "Airflow", "Kafka"
]

DEGREE_PATTERNS = [
    "Bachelor of Science", "B.S.", "BS in Computer Science", "Bachelor of Engineering", "B.E.", "B.Tech",
    "Master of Science", "M.S.", "MS in Software Engineering", "Master of Business Administration", "MBA",
    "Ph.D.", "PhD in Computer Science", "Doctor of Philosophy", "Associate Degree", "Diploma in Computer Applications",
    "Bachelor of Arts", "B.A.", "Master of Technology", "M.Tech", "Bachelor's Degree", "Master's Degree"
]

EXPERIENCE_PATTERNS = [
    "Software Engineer", "Senior Software Engineer", "Backend Developer", "Frontend Developer", "Full Stack Developer",
    "DevOps Engineer", "Cloud Architect", "Data Scientist", "Machine Learning Engineer", "AI Researcher",
    "Technical Lead", "Tech Lead", "Engineering Manager", "Product Manager", "QA Engineer", "Database Administrator",
    "System Administrator", "Solutions Architect", "Intern", "Software Engineering Intern", "Junior Developer"
]

# Training samples for spaCy custom NER
TRAIN_DATA = [
    (
        "John Doe is a Senior Software Engineer with 5 years experience in Python, Django, PostgreSQL, and AWS.",
        {"entities": [(14, 38, "EXPERIENCE"), (55, 61, "SKILL"), (63, 69, "SKILL"), (71, 81, "SKILL"), (87, 90, "SKILL")]}
    ),
    (
        "Graduated with a Bachelor of Science in Computer Science from MIT in May 2021.",
        {"entities": [(17, 52, "DEGREE"), (69, 77, "DATE")]}
    ),
    (
        "Worked as a Machine Learning Engineer at Acme Corp from January 2022 to Present building PyTorch models.",
        {"entities": [(12, 37, "EXPERIENCE"), (51, 74, "DATE"), (89, 96, "SKILL")]}
    ),
    (
        "Proficient in Docker, Kubernetes, CI/CD, Terraform, and Go microservices.",
        {"entities": [(14, 20, "SKILL"), (22, 32, "SKILL"), (34, 39, "SKILL"), (41, 50, "SKILL"), (56, 58, "SKILL"), (59, 72, "SKILL")]}
    ),
    (
        "Earned a Master of Science in Data Science between 2019 and 2021.",
        {"entities": [(9, 41, "DEGREE"), (50, 64, "DATE")]}
    ),
    (
        "Lead DevOps Engineer managing Kubernetes clusters on AWS and Google Cloud from 2020 to 2024.",
        {"entities": [(0, 19, "EXPERIENCE"), (29, 39, "SKILL"), (52, 55, "SKILL"), (60, 72, "SKILL"), (78, 90, "DATE")]}
    ),
    (
        "Completed B.Tech in Information Technology with honors in June 2018.",
        {"entities": [(10, 41, "DEGREE"), (57, 66, "DATE")]}
    ),
    (
        "Full Stack Developer specializing in React, Next.js, Node.js, and MongoDB.",
        {"entities": [(0, 20, "EXPERIENCE"), (37, 42, "SKILL"), (44, 51, "SKILL"), (53, 60, "SKILL"), (66, 73, "SKILL")]}
    )
]

_nlp_model = None

def get_or_train_custom_ner() -> spacy.language.Language:
    """
    Loads the trained custom NER model from disk, or builds and trains it if not present.
    """
    global _nlp_model
    if _nlp_model is not None:
        return _nlp_model

    if MODEL_DIR.exists() and (MODEL_DIR / "config.cfg").exists():
        try:
            _nlp_model = spacy.load(MODEL_DIR)
            return _nlp_model
        except Exception as e:
            print(f"Warning: Failed loading saved model from {MODEL_DIR}: {e}. Retraining...")

    # Build and fine-tune model using base English model + EntityRuler + NER pipeline
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = spacy.blank("en")

    # Add EntityRuler with comprehensive patterns before ner
    if "ner" in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner")
    else:
        ruler = nlp.add_pipe("entity_ruler")

    patterns = []
    for skill in SKILL_PATTERNS:
        patterns.append({"label": "SKILL", "pattern": skill})
        patterns.append({"label": "SKILL", "pattern": skill.lower()})

    for deg in DEGREE_PATTERNS:
        patterns.append({"label": "DEGREE", "pattern": deg})

    for exp in EXPERIENCE_PATTERNS:
        patterns.append({"label": "EXPERIENCE", "pattern": exp})

    # Common date regexes
    date_regexes = [
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b",
        r"\b\d{4}\s*[-–—to]+\s*(?:\d{4}|Present|Current|Now)\b",
        r"\b(?:20|19)\d{2}\b"
    ]
    for dr in date_regexes:
        patterns.append({"label": "DATE", "pattern": [{"TEXT": {"REGEX": dr}}]})

    ruler.add_patterns(patterns)

    # Train NER component if available
    if "ner" in nlp.pipe_names:
        ner = nlp.get_pipe("ner")
        for _, annotations in TRAIN_DATA:
            for ent in annotations.get("entities"):
                ner.add_label(ent[2])

        # Optimize for 15 iterations on sample data
        import random
        from spacy.util import minibatch, compounding
        other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in ["ner", "entity_ruler"]]
        with nlp.disable_pipes(*other_pipes):
            optimizer = nlp.resume_training()
            for itn in range(12):
                random.shuffle(TRAIN_DATA)
                losses = {}
                for text, annotations in TRAIN_DATA:
                    example = Example.from_dict(nlp.make_doc(text), annotations)
                    nlp.update([example], drop=0.2, losses=losses, sgd=optimizer)

    # Save compiled model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(MODEL_DIR)
    _nlp_model = nlp
    return _nlp_model


def extract_entities_from_text(text: str) -> Dict[str, Any]:
    """
    Arranges extracted resume text into fields: SKILL, DEGREE, EXPERIENCE, DATE.
    Returns categorized unique entities and highlighted span data.
    """
    if not text:
        return {"SKILL": [], "DEGREE": [], "EXPERIENCE": [], "DATE": [], "spans": []}

    nlp = get_or_train_custom_ner()
    doc = nlp(text)

    entities_by_label: Dict[str, List[str]] = {
        "SKILL": [],
        "DEGREE": [],
        "EXPERIENCE": [],
        "DATE": []
    }
    spans: List[Dict[str, Any]] = []

    # Regex heuristic for dates if missed by model
    date_matches = re.finditer(
        r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b|\b\d{4}\s*[-–—to]+\s*(?:\d{4}|Present|Current|Now)\b',
        text,
        flags=re.IGNORECASE
    )
    for dm in date_matches:
        d_val = dm.group().strip()
        if d_val not in entities_by_label["DATE"]:
            entities_by_label["DATE"].append(d_val)

    for ent in doc.ents:
        label = ent.label_
        val = ent.text.strip()
        if label in entities_by_label:
            if val and val not in entities_by_label[label]:
                entities_by_label[label].append(val)
            spans.append({
                "text": val,
                "label": label,
                "start": ent.start_char,
                "end": ent.end_char
            })

    # Sort spans by occurrence in text
    spans.sort(key=lambda s: s["start"])

    return {
        "SKILL": sorted(list(set(entities_by_label["SKILL"]))),
        "DEGREE": sorted(list(set(entities_by_label["DEGREE"]))),
        "EXPERIENCE": sorted(list(set(entities_by_label["EXPERIENCE"]))),
        "DATE": sorted(list(set(entities_by_label["DATE"]))),
        "spans": spans
    }
