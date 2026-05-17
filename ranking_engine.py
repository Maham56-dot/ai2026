from typing import List, Dict, Any

class RankingEngine:
    """
    Advanced Ranking Algorithm for Service Providers.
    Calculates a weighted score based on 6+ factors:
    1. Distance
    2. Travel Time
    3. Availability
    4. Skill Specialization
    5. Reliability Score
    6. User Risk Score
    """

    def __init__(self, weights: Dict[str, float] = None):
        # Default weights for the ranking algorithm. Can be tuned.
        self.weights = weights or {
            "distance": 0.15,
            "travel_time": 0.20,
            "availability": 0.20,
            "skill_match": 0.25,
            "reliability": 0.15,
            "user_risk_penalty": 0.05
        }

    def _score_distance(self, distance_km: float, max_distance: float = 20.0) -> float:
        """Score decreases as distance increases."""
        if distance_km >= max_distance:
            return 0.0
        return max(0.0, 1.0 - (distance_km / max_distance))

    def _score_travel_time(self, travel_time_mins: float, max_time: float = 60.0) -> float:
        """Score decreases as travel time increases."""
        if travel_time_mins >= max_time:
            return 0.0
        return max(0.0, 1.0 - (travel_time_mins / max_time))

    def _score_availability(self, status: str) -> float:
        """Availability scoring based on immediate readiness."""
        status = status.lower()
        if status == "available_now":
            return 1.0
        elif status == "available_soon":
            return 0.7
        elif status == "busy":
            return 0.2
        return 0.0

    def _score_skill(self, required_level: str, provider_level: str) -> float:
        """
        Levels: 'Basic', 'Intermediate', 'Complex'
        If provider matches perfectly: 1.0
        If provider is overqualified: 0.8
        If provider is underqualified: 0.0
        """
        levels = {"basic": 1, "intermediate": 2, "complex": 3}
        req_val = levels.get(required_level.lower(), 1)
        prov_val = levels.get(provider_level.lower(), 1)

        if prov_val == req_val:
            return 1.0
        elif prov_val > req_val:
            return 0.8  # Overqualified, good but might be more expensive
        else:
            return 0.0  # Underqualified

    def _score_reliability(self, on_time_rate: float) -> float:
        """Direct 0.0 to 1.0 mapping representing historical on-time rate."""
        return max(0.0, min(1.0, on_time_rate))

    def _apply_risk_penalty(self, user_risk_score: float, provider_reliability: float) -> float:
        """
        If a User has a high Risk Score (e.g., historically problematic, cancels often), 
        we might penalize matching them with low reliability providers to prevent total failure.
        user_risk_score: 0.0 (safe) to 1.0 (risky)
        """
        # A risky user matched with a low-reliability provider gets a heavy penalty.
        risk_mismatch = user_risk_score * (1.0 - provider_reliability)
        return max(0.0, 1.0 - risk_mismatch)

    def rank_providers(self, job_context: Dict[str, Any], providers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculates the final score for each provider and returns the sorted list.
        """
        ranked_list = []
        for p in providers:
            s_dist = self._score_distance(p.get("distance_km", 10.0))
            s_time = self._score_travel_time(p.get("travel_time_mins", 30.0))
            s_avail = self._score_availability(p.get("availability", "available_now"))
            s_skill = self._score_skill(job_context.get("required_skill_level", "Basic"), p.get("skill_level", "Basic"))
            s_rel = self._score_reliability(p.get("on_time_rate", 0.8))
            s_risk = self._apply_risk_penalty(job_context.get("user_risk_score", 0.0), s_rel)

            # Check hard constraints
            if s_skill == 0.0:
                continue # Skip underqualified providers

            # Complexity Matching Constraint
            job_complexity = job_context.get("complexity", "Basic")
            if job_complexity.lower() == "complex":
                is_senior = p.get("experience_level", "").lower() == "senior" or any("senior" in c.lower() for c in p.get("certifications", []))
                has_high_exp_tools = p.get("has_high_experience_tools", False)
                if not (is_senior or has_high_exp_tools):
                    continue # Complex jobs strictly require Senior certification or high experience tools

            # Weighted sum
            final_score = (
                (s_dist * self.weights["distance"]) +
                (s_time * self.weights["travel_time"]) +
                (s_avail * self.weights["availability"]) +
                (s_skill * self.weights["skill_match"]) +
                (s_rel * self.weights["reliability"]) +
                (s_risk * self.weights["user_risk_penalty"])
            )
            
            # Normalize to account for weights potentially not summing exactly to 1, though they should
            total_weight = sum(self.weights.values())
            normalized_score = final_score / total_weight

            p_copy = p.copy()
            p_copy["ranking_score"] = normalized_score
            p_copy["score_breakdown"] = {
                "distance": s_dist,
                "travel_time": s_time,
                "availability": s_avail,
                "skill_match": s_skill,
                "reliability": s_rel,
                "user_risk_penalty": s_risk
            }
            ranked_list.append(p_copy)

        # Sort descending by ranking_score
        ranked_list.sort(key=lambda x: x["ranking_score"], reverse=True)
        return ranked_list

# Example Usage
if __name__ == "__main__":
    engine = RankingEngine()
    
    job_context = {
        "required_skill_level": "Intermediate",
        "user_risk_score": 0.4 # A slightly risky user
    }
    
    mock_providers = [
        {
            "id": "p1", "name": "Ali Plumbers", 
            "distance_km": 2.5, "travel_time_mins": 10.0, 
            "availability": "available_now", "skill_level": "Intermediate", 
            "on_time_rate": 0.95
        },
        {
            "id": "p2", "name": "Zain Services", 
            "distance_km": 8.0, "travel_time_mins": 25.0, 
            "availability": "available_now", "skill_level": "Complex", 
            "on_time_rate": 0.80
        },
        {
            "id": "p3", "name": "Farhan Fixers", 
            "distance_km": 1.0, "travel_time_mins": 5.0, 
            "availability": "busy", "skill_level": "Basic", # Should be filtered out due to low skill
            "on_time_rate": 0.90
        }
    ]
    
    results = engine.rank_providers(job_context, mock_providers)
    
    print("Ranking Results:")
    for idx, r in enumerate(results, 1):
        print(f"{idx}. {r['name']} - Score: {r['ranking_score']:.3f} | Breakdown: {r['score_breakdown']}")
