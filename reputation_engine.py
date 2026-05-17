import json
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

class ReputationEngine:
    """
    Post-service Reputation & Feedback Engine for AI Service Orchestrator.
    Collects user star ratings and sentiment-based text reviews.
    Automatically parses Roman Urdu & English feedback to adjust provider averages 
    and reliability metrics in a persistent disk database.
    """

    def __init__(self, providers_db_path: str = "providers_db.json", reviews_log_path: str = "reviews_log.json"):
        self.providers_db_path = providers_db_path
        self.reviews_log_path = reviews_log_path
        
        # Initialize review log file if it does not exist
        if not os.path.exists(self.reviews_log_path):
            self._write_reviews([])
            
        # Define Roman Urdu & English Sentiment Dictionaries
        self.positive_lexicon = {
            # English
            "good", "great", "excellent", "professional", "best", "amazing", "perfect", 
            "fast", "polite", "expert", "quick", "happy", "satisfied", "recommend", "neat", "honest",
            # Roman Urdu
            "acha", "achha", "behtareen", "zabardast", "fit", "shukriya", "teek", "theek", 
            "kamyab", "safai", "imandari", "jaldi", "tameez", "khush", "zabar-dast", "shandar"
        }
        
        self.negative_lexicon = {
            # English
            "bad", "worst", "terrible", "poor", "late", "slow", "expensive", "rude", 
            "unprofessional", "damage", "waste", "unhappy", "problem", "issue", "dirty", "untrustworthy",
            # Roman Urdu
            "kharab", "bekar", "bekaar", "ganda", "der", "bura", "mehenga", "mhenga", 
            "badtameez", "nuqsan", "masla", "zaya", "faltu", "late", "nuksan"
        }

    def _load_providers(self) -> List[Dict[str, Any]]:
        """Loads providers profiles from persistent database on disk."""
        try:
            with open(self.providers_db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_providers(self, providers: List[Dict[str, Any]]):
        """Saves providers profiles back to the persistent database."""
        try:
            with open(self.providers_db_path, "w", encoding="utf-8") as f:
                json.dump(providers, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save providers database: {e}")

    def _load_reviews(self) -> List[Dict[str, Any]]:
        """Loads reviews history ledger from disk."""
        try:
            with open(self.reviews_log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_reviews(self, reviews: List[Dict[str, Any]]):
        """Writes reviews history ledger back to disk."""
        try:
            with open(self.reviews_log_path, "w", encoding="utf-8") as f:
                json.dump(reviews, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to write reviews log: {e}")

    def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves provider statistics by ID."""
        providers = self._load_providers()
        for p in providers:
            if p.get("id") == provider_id:
                return p
        return None

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyzes Roman Urdu & English review text lexical structure.
        Returns a score in range [-1.0, 1.0] and a sentiment categorization label.
        """
        if not text or not text.strip():
            return {"score": 0.0, "label": "Neutral"}

        text_lower = text.lower()
        
        # Simple bigram substitutions for Roman Urdu common intensifiers
        text_lower = text_lower.replace("bohot acha", "behtareen")
        text_lower = text_lower.replace("buhut acha", "behtareen")
        text_lower = text_lower.replace("bohat acha", "behtareen")
        text_lower = text_lower.replace("bohot late", "der")
        text_lower = text_lower.replace("buhut late", "der")
        
        # Tokenize by removing simple punctuation and splitting spaces
        for char in [".", ",", "!", "?", ";", ":", "-", "(", ")", "\"", "'"]:
            text_lower = text_lower.replace(char, " ")
            
        words = text_lower.split()
        
        pos_count = 0
        neg_count = 0
        
        for w in words:
            if w in self.positive_lexicon:
                pos_count += 1
            elif w in self.negative_lexicon:
                neg_count += 1

        total = pos_count + neg_count
        if total == 0:
            score = 0.0
            label = "Neutral"
        else:
            score = (pos_count - neg_count) / total
            if score > 0.20:
                label = "Positive"
            elif score < -0.20:
                label = "Negative"
            else:
                label = "Neutral"

        return {
            "score": round(score, 2),
            "label": label,
            "matched_positive_count": pos_count,
            "matched_negative_count": neg_count
        }

    def submit_feedback(
        self,
        job_id: str,
        provider_id: str,
        rating: float,
        review_text: str
    ) -> Dict[str, Any]:
        """
        Ingests post-service user feedback.
        Analyzes sentiment, updates the provider average ratings, shifts reliability score,
        saves to provider database, and appends a record in the reviews transaction ledger.
        """
        # Validate rating boundary
        rating = max(1.0, min(5.0, float(rating)))

        # 1. Run Sentiment Analysis
        sentiment = self.analyze_sentiment(review_text)
        sentiment_score = sentiment["score"]
        sentiment_label = sentiment["label"]

        # 2. Load providers registry
        providers = self._load_providers()
        matched_provider = None
        
        old_rating = 0.0
        new_rating = 0.0
        old_total_reviews = 0
        old_reliability = 0.0
        new_reliability = 0.0

        for p in providers:
            if p.get("id") == provider_id:
                matched_provider = p
                break
                
        if not matched_provider:
            return {"success": False, "error_message": f"Provider with ID '{provider_id}' not found."}

        # 3. Calculate Math Rating Averages
        old_rating = matched_provider.get("rating", 4.0)
        old_total_reviews = matched_provider.get("user_ratings_total", 0)
        old_reliability = matched_provider.get("on_time_rate", 0.85)

        new_total_reviews = old_total_reviews + 1
        new_rating = ((old_rating * old_total_reviews) + rating) / new_total_reviews

        # 4. Calculate Reliability Score / Reputation Index adjustment
        # High rating + Positive sentiment yields moderate increase
        # Low rating + Negative sentiment yields heavy decrease
        reliability_change = 0.0
        if rating >= 4.0 and sentiment_score > 0.0:
            reliability_change = sentiment_score * 0.02
        elif rating <= 2.0 and sentiment_score < 0.0:
            reliability_change = sentiment_score * 0.05 # sentiment_score is negative, so subtracts
        elif rating <= 2.0:
            # Surcharge rating penalty even if sentiment wasn't matched
            reliability_change = -0.03
            
        new_reliability = old_reliability + reliability_change
        # Clip reliability strictly between 0.50 (minimum benchmark) and 1.00 (perfect index)
        new_reliability = max(0.50, min(1.00, new_reliability))

        # 5. Mutate Provider Record
        matched_provider["rating"] = round(new_rating, 2)
        matched_provider["user_ratings_total"] = new_total_reviews
        matched_provider["on_time_rate"] = round(new_reliability, 3)

        # Write provider updates back to providers_db.json
        self._save_providers(providers)

        # 6. Append feedback record to reviews transaction ledger
        review_record = {
            "timestamp": datetime.now().isoformat(),
            "job_id": job_id,
            "provider_id": provider_id,
            "provider_name": matched_provider.get("name", "Unknown"),
            "rating": rating,
            "review_text": review_text,
            "sentiment": sentiment,
            "rating_delta": {
                "old_rating": old_rating,
                "new_rating": round(new_rating, 2),
                "total_reviews": new_total_reviews
            },
            "reliability_delta": {
                "old_reliability": old_reliability,
                "new_reliability": round(new_reliability, 3),
                "adjustment": round(reliability_change, 3)
            }
        }
        
        reviews = self._load_reviews()
        reviews.append(review_record)
        self._write_reviews(reviews)

        return {
            "success": True,
            "provider_name": matched_provider.get("name"),
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "rating_delta": review_record["rating_delta"],
            "reliability_delta": review_record["reliability_delta"],
            "review_record": review_record
        }

# Local manual test execution
if __name__ == "__main__":
    # Setup temp engine
    rep_eng = ReputationEngine(providers_db_path="providers_db.json", reviews_log_path="test_reviews_log.json")
    
    # Analyze sentiment
    r1 = rep_eng.analyze_sentiment("Zafar Ali is an excellent electrician, bohot acha kaam kiya jaldi mein!")
    print(f"Bilingual review sentiment: {r1['score']} ({r1['label']})")
    
    r2 = rep_eng.analyze_sentiment("terrible service, bekaar banda late aya aur kaam kharab kiya")
    print(f"Bilingual review sentiment: {r2['score']} ({r2['label']})")
    
    # Submit feedback mock
    f_res = rep_eng.submit_feedback(
        job_id="JOB-POST-999",
        provider_id="prov_02", # Yasir Plumber
        rating=5.0,
        review_text="bohot zabardast pipe fit kiya, shukriya Yasir sahib!"
    )
    print("\nFeedback submit response:")
    print(f"  Success:       {f_res['success']}")
    print(f"  Sentiment:     {f_res['sentiment_score']} ({f_res['sentiment_label']})")
    print(f"  Rating Shift:  {f_res['rating_delta']['old_rating']} -> {f_res['rating_delta']['new_rating']} (Reviews: {f_res['rating_delta']['total_reviews']})")
    print(f"  Reliability:   {f_res['reliability_delta']['old_reliability']} -> {f_res['reliability_delta']['new_reliability']} (Adj: {f_res['reliability_delta']['adjustment']})")
    
    # Clean reviews log
    if os.path.exists("test_reviews_log.json"):
        os.remove("test_reviews_log.json")
