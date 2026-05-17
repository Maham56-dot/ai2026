import http.server
import socketserver
import json
import urllib.parse
import sys
from datetime import datetime, timedelta

# Import backend modules
from ranking_engine import RankingEngine
from pricing_engine import PricingEngine
from scheduling_engine import SchedulingEngine
from tracking_engine import TrackingEngine
from reputation_engine import ReputationEngine
from dispute_engine import DisputeEngine

PORT = 8000

# Initialize engines statefully
ranking_engine = RankingEngine()
pricing_engine = PricingEngine(cost_per_km=50.0, base_travel_overhead=100.0)
scheduling_engine = SchedulingEngine(buffer_minutes=30)
tracking_engine = TrackingEngine(log_path="tracking_log.json")
reputation_engine = ReputationEngine(providers_db_path="providers_db.json", reviews_log_path="reviews_log.json")
dispute_engine = DisputeEngine(disputes_log_path="disputes_log.json")

class RESTAPIServer(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Override to suppress standard terminal logs, making it cleaner
        sys.stdout.write(f"🛰️ REST Server - {datetime.now().strftime('%H:%M:%S')} - {format%args}\n")

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        self._set_cors_headers()
        
        # Serve SPA mobile frontend
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            except Exception as e:
                self.wfile.write(f"<h2>Failed to load index.html: {e}</h2>".encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        self._set_cors_headers()
        
        # Read request body
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            req_data = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            req_data = {}

        response_body = {"success": False, "error_message": "Invalid Route"}
        status_code = 404

        # Route 1: NLU Intent Mapping & Provider matching
        if self.path == "/api/nlu":
            status_code = 200
            query = req_data.get("query", "").lower()
            urgency = req_data.get("urgency", "Medium")
            complexity = req_data.get("complexity", "Intermediate")
            booking_hour = req_data.get("booking_hour", 12)
            
            # Basic query mapping keyword rules
            if "light" in query or "electric" in query or "bijli" in query or "wire" in query:
                resolved_service = "electrician"
            elif "plumb" in query or "pipe" in query or "leak" in query or "sewer" in query or "flush" in query:
                resolved_service = "plumbing"
            elif "ac" in query or "cooling" in query or "ref" in query:
                resolved_service = "ac repair"
            else:
                resolved_service = "electrician" # standard fallback

            job_ctx = {
                "required_skill_level": complexity,
                "complexity": complexity,
                "user_risk_score": 0.1,
                "urgency": urgency,
                "booking_hour": booking_hour
            }
            
            # Load provider db profiles dynamically
            providers = reputation_engine._load_providers()
            
            # Specialty filters
            specialized = []
            for p in providers:
                name_lower = p["name"].lower()
                if resolved_service == "electrician" and "electrician" in name_lower:
                    specialized.append(p)
                elif resolved_service == "plumbing" and "plumber" in name_lower:
                    specialized.append(p)
                elif resolved_service == "ac repair" and "ac" in name_lower:
                    specialized.append(p)
                else:
                    # In case of generic unmatched items, provide all
                    specialized.append(p)
                    
            if not specialized:
                # If filter yielded empty, revert to all providers
                specialized = providers

            ranked_list = ranking_engine.rank_providers(job_ctx, specialized)
            response_body = {
                "success": True,
                "service": resolved_service,
                "urgency": urgency,
                "complexity": complexity,
                "providers": ranked_list
            }

        # Route 2: Pricing Calculations & Alternatives
        elif self.path == "/api/pricing":
            status_code = 200
            provider_id = req_data.get("provider_id")
            urgency = req_data.get("urgency", "Medium")
            complexity = req_data.get("complexity", "Intermediate")
            booking_hour = req_data.get("booking_hour", 12)
            distance_km = req_data.get("distance_km")

            providers = reputation_engine._load_providers()
            matched_prov = next((p for p in providers if p["id"] == provider_id), None)
            
            if matched_prov:
                prov_override = matched_prov.copy()
                if distance_km is not None:
                    prov_override["distance_km"] = float(distance_km)
                    
                job_context = {
                    "urgency": urgency,
                    "complexity": complexity,
                    "booking_hour": int(booking_hour)
                }
                
                price_analysis = pricing_engine.calculate_pricing(prov_override, job_context)
                response_body = {
                    "success": True,
                    "pricing": price_analysis
                }
            else:
                response_body = {"success": False, "error_message": f"Provider '{provider_id}' not found."}

        # Route 3: Scheduling / Calendar reservation
        elif self.path == "/api/book":
            status_code = 200
            provider_id = req_data.get("provider_id")
            provider_name = req_data.get("provider_name")
            job_id = req_data.get("job_id", f"JOB-{datetime.now().strftime('%M%S')}")
            urgency = req_data.get("urgency", "Medium")
            location = req_data.get("location", "Sector F-8, Islamabad")
            price = req_data.get("price", 1000.0)
            user_contact = req_data.get("user_contact", "+92 300 1234567")
            
            # Setup booking slot for tomorrow 10:00 AM
            tomorrow = datetime.now() + timedelta(days=1)
            booking_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            
            booking_res = scheduling_engine.book_slot(
                provider_id=provider_id,
                provider_name=provider_name,
                job_id=job_id,
                start_time=booking_time,
                duration_mins=60,
                user_contact=user_contact,
                urgency=urgency.capitalize(),
                location=location,
                price=float(price)
            )
            
            if booking_res["success"]:
                # Log initial status tracking transitions
                tracking_engine.update_status(job_id, provider_id, provider_name, tracking_engine.PENDING, location=location)
                tracking_engine.update_status(job_id, provider_id, provider_name, tracking_engine.ACCEPTED, location=location)
                
                response_body = {
                    "success": True,
                    "job_id": job_id,
                    "booking": booking_res
                }
            else:
                response_body = {
                    "success": False,
                    "error_message": booking_res.get("error_message"),
                    "error_message_ur": booking_res.get("error_message_ur")
                }

        # Route 4: Real-time status timeline tracking simulator
        elif self.path == "/api/track":
            status_code = 200
            job_id = req_data.get("job_id")
            provider_id = req_data.get("provider_id")
            provider_name = req_data.get("provider_name")
            new_status = req_data.get("new_status")
            location = req_data.get("location", "Sector F-8, Islamabad")
            eta_minutes = req_data.get("eta_minutes")

            try:
                kwargs = {}
                if eta_minutes is not None:
                    kwargs["eta_minutes"] = int(eta_minutes)
                    
                event = tracking_engine.update_status(
                    job_id=job_id,
                    provider_id=provider_id,
                    provider_name=provider_name,
                    new_status=new_status,
                    location=location,
                    **kwargs
                )
                response_body = {
                    "success": True,
                    "latest_event": event
                }
            except Exception as e:
                response_body = {
                    "success": False,
                    "error_message": str(e)
                }

        # Route 5: Ingest ratings and Roman Urdu Sentiment Feedback
        elif self.path == "/api/rate":
            status_code = 200
            job_id = req_data.get("job_id")
            provider_id = req_data.get("provider_id")
            rating = float(req_data.get("rating", 5.0))
            review_text = req_data.get("review_text", "")

            fed_res = reputation_engine.submit_feedback(
                job_id=job_id,
                provider_id=provider_id,
                rating=rating,
                review_text=review_text
            )
            response_body = fed_res

        # Route 6: Register Dispute escalations
        elif self.path == "/api/dispute":
            status_code = 200
            job_id = req_data.get("job_id")
            provider_id = req_data.get("provider_id")
            provider_name = req_data.get("provider_name")
            customer_contact = req_data.get("customer_contact", "+923001234567")
            category = req_data.get("category", DisputeEngine.POOR_QUALITY)
            customer_complaint = req_data.get("customer_complaint", "")
            billing_info = req_data.get("billing_info")
            provider_stats = req_data.get("provider_stats")

            try:
                ticket = dispute_engine.raise_dispute(
                    job_id=job_id,
                    provider_id=provider_id,
                    provider_name=provider_name,
                    customer_contact=customer_contact,
                    category=category,
                    customer_complaint=customer_complaint,
                    billing_info=billing_info,
                    provider_stats=provider_stats
                )
                response_body = {
                    "success": True,
                    "ticket": ticket
                }
            except Exception as e:
                response_body = {
                    "success": False,
                    "error_message": str(e)
                }

        # Send response
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(response_body, ensure_ascii=False).encode("utf-8"))

def run_server():
    server_address = ('', PORT)
    # Reconfigure UTF-8 console output overrides to avoid crash triggers on Windows CMD
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        
    print("\n" + "=" * 60)
    print(f"🚀 AI SERVICE ORCHESTRATOR FULL-STACK API SERVER RUNNING")
    print(f"👉 Local Web Access: http://localhost:{PORT}")
    print(f"👉 Rest APIs endpoint triggers: http://localhost:{PORT}/api")
    print("👉 Use CTRL+C in the terminal to close the active server")
    print("=" * 60 + "\n")
    
    with socketserver.TCPServer(server_address, RESTAPIServer) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🚨 Shutting down active API REST Server safely. Goodbye!")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
