import json
import re
from collections import Counter
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer


FALLBACK_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "using",
    "with",
}


class TextProcessor:
    def __init__(self, model_name: str, skill_lexicon_path: str):
        self.nlp, self.supports_spacy = self._load_nlp(model_name)
        self.skill_lexicon = self._load_skill_lexicon(skill_lexicon_path)
        self.skill_terms = sorted(
            {skill.lower() for skills in self.skill_lexicon.values() for skill in skills},
            key=len,
            reverse=True,
        )
        self.matcher = None
        if self.supports_spacy:
            from spacy.matcher import PhraseMatcher

            self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            patterns = [self.nlp.make_doc(skill) for skill in self.skill_terms]
            if patterns:
                self.matcher.add("SKILLS", patterns)

    @staticmethod
    def _load_nlp(model_name: str):
        try:
            import spacy

            return spacy.load(model_name), True
        except Exception:
            return None, False

    @staticmethod
    def _load_skill_lexicon(skill_lexicon_path: str) -> dict:
        with Path(skill_lexicon_path).open("r", encoding="utf-8") as file:
            return json.load(file)

    def clean_text(self, text: str) -> str:
        normalized = re.sub(r"\s+", " ", text).strip().lower()
        if not normalized:
            return ""

        if not self.supports_spacy:
            tokens = re.findall(r"[a-z0-9+#.\-]+", normalized)
            filtered = [token for token in tokens if token not in FALLBACK_STOPWORDS]
            return " ".join(filtered)

        doc = self.nlp(normalized)
        lemmas = []
        for token in doc:
            if token.is_space or token.is_punct or token.is_stop:
                continue
            lemma = token.lemma_.strip().lower() if token.lemma_ else token.text.lower()
            if lemma and lemma != "-pron-":
                lemmas.append(lemma)
        return " ".join(lemmas)

    def extract_skills(self, text: str) -> list[str]:
        token_text = f" {text.lower()} "
        found = set()

        if self.supports_spacy and self.matcher is not None:
            from spacy.util import filter_spans

            doc = self.nlp(text.lower())
            matches = self.matcher(doc)
            spans = filter_spans([doc[start:end] for _, start, end in matches])
            found.update({span.text.strip().lower() for span in spans if span.text.strip()})

        for skill in self.skill_terms:
            if re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", token_text):
                found.add(skill)

        return sorted(found)

    def extract_keywords(self, text: str, limit: int = 10) -> list[str]:
        cleaned = self.clean_text(text)
        if not cleaned:
            return []

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=50)
        matrix = vectorizer.fit_transform([cleaned])
        scores = matrix.toarray()[0]
        feature_names = vectorizer.get_feature_names_out()

        weighted_terms = sorted(
            zip(feature_names, scores), key=lambda item: item[1], reverse=True
        )
        return [term for term, score in weighted_terms if score > 0][:limit]

    def detect_candidate_name(self, text: str, filename: str) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if 1 <= len(first_line.split()) <= 4 and len(first_line) <= 60:
            return first_line.title()

        stem = Path(filename).stem.replace("_", " ").replace("-", " ").strip()
        if stem:
            return stem.title()

        return "Unknown Candidate"

    def top_skill_categories(self, skills: list[str]) -> Counter:
        lower_skills = {skill.lower() for skill in skills}
        categories = Counter()
        for category, category_skills in self.skill_lexicon.items():
            overlap = lower_skills.intersection({skill.lower() for skill in category_skills})
            if overlap:
                categories[category] = len(overlap)
        return categories
