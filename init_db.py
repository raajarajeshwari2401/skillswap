"""Database initialization and seeding script for SkillSwap.
Populates standard academic categories, demo users, sample skill offers with SymPy points,
and securely provisions the initial administrator account.
"""

import os
import json
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.skill import SkillCategory, SkillOffer, SkillRequest
from app.services.wallet_service import wallet_service
from app.services.scoring_service import scoring_service

app = create_app(os.environ.get("FLASK_ENV", "development"))


def seed_database():
    with app.app_context():
        print("[*] Creating all database tables...")
        db.create_all()

        # 1. Seed Academic Categories
        categories_data = [
            {"name": "Computer Science & Programming", "slug": "programming", "description": "Python, Web Dev, Algorithms, C++, Git", "icon": "code"},
            {"name": "Mathematics & Statistics", "slug": "mathematics", "description": "Calculus, Linear Algebra, Probability, Statistics", "icon": "calculator"},
            {"name": "Languages & Writing", "slug": "languages", "description": "Spanish, French, Essay Editing, Public Speaking", "icon": "globe"},
            {"name": "Design & Digital Media", "slug": "design", "description": "UI/UX, Figma, Adobe Photoshop, Video Editing", "icon": "palette"},
            {"name": "Music & Creative Arts", "slug": "music", "description": "Guitar, Piano, Music Theory, Audio Production", "icon": "music"},
            {"name": "Business & Economics", "slug": "business", "description": "Microeconomics, Accounting, Financial Modeling", "icon": "briefcase"},
        ]

        categories_map = {}
        for cat in categories_data:
            existing = SkillCategory.query.filter_by(slug=cat["slug"]).first()
            if not existing:
                cat_obj = SkillCategory(**cat)
                db.session.add(cat_obj)
                db.session.flush()
                categories_map[cat["slug"]] = cat_obj
            else:
                categories_map[cat["slug"]] = existing

        # 2. Seed Initial Administrator (Securely from Environment Variables)
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@skillswap.edu").lower()
        admin_password = os.environ.get("ADMIN_PASSWORD", "AdminSecurePass2026!")
        admin_name = os.environ.get("ADMIN_NAME", "System Administrator")

        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                email=admin_email,
                full_name=admin_name,
                location="Campus Administration",
                is_admin=True,
                bio="Platform system administrator.",
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.flush()
            wallet_service.create_wallet_for_user(admin_user.id, initial_points=100.0)
            print(f"[+] Created Administrator account: {admin_email}")

        # 3. Seed Demo College Students
        demo_students = [
            {
                "full_name": "Maya Lin",
                "email": "maya@skillswap.edu",
                "password": "Password123!",
                "location": "Engineering Hall / Remote",
                "bio": "Senior CS Major. Passionate about web development, clean architecture, and algorithmic problem solving.",
            },
            {
                "full_name": "Ethan Chen",
                "email": "ethan@skillswap.edu",
                "password": "Password123!",
                "location": "North Campus Quad / Science Library",
                "bio": "Junior Applied Mathematics & Physics double major. Love breaking down complex proofs into intuitive concepts.",
            },
            {
                "full_name": "Sophia Rodriguez",
                "email": "sophia@skillswap.edu",
                "password": "Password123!",
                "location": "Design Media Center / Remote",
                "bio": "Sophomore Graphic Design & Interactive Media. Freelance designer proficient in Figma, typography, and wireframing.",
            },
        ]

        users_map = {}
        for student in demo_students:
            u = User.query.filter_by(email=student["email"]).first()
            if not u:
                u = User(
                    full_name=student["full_name"],
                    email=student["email"],
                    location=student["location"],
                    bio=student["bio"],
                )
                u.set_password(student["password"])
                db.session.add(u)
                db.session.flush()
                wallet_service.create_wallet_for_user(u.id, initial_points=50.0)
                print(f"[+] Created student account: {u.full_name} ({u.email})")
            users_map[student["email"]] = u

        # 4. Seed Sample Skill Offers with Live SymPy Calculations
        sample_offers = [
            {
                "email": "maya@skillswap.edu",
                "cat_slug": "programming",
                "title": "Python & Flask Web Application Architecture",
                "description": "Learn to construct RESTful web applications using Python Flask, Jinja2 templates, and SQLAlchemy ORM models. We will build a working CRUD app together.",
                "proficiency_level": "intermediate",
                "duration_minutes": 60,
                "preparation_effort": 1,
                "interaction_mode": "hybrid",
                "location_details": "Computer Science Lab 102 or Zoom",
            },
            {
                "email": "ethan@skillswap.edu",
                "cat_slug": "mathematics",
                "title": "Calculus II: Integration Techniques & Series Convergence",
                "description": "Master integration by parts, trigonometric substitutions, and power series. We will work through past exam problems together with clear step-by-step proofs.",
                "proficiency_level": "intermediate",
                "duration_minutes": 60,
                "preparation_effort": 2,
                "interaction_mode": "offline",
                "location_details": "Math Library Study Room 4",
            },
            {
                "email": "sophia@skillswap.edu",
                "cat_slug": "design",
                "title": "Figma UI/UX Prototyping & Design Systems",
                "description": "Hands-on tutorial creating interactive college app prototypes in Figma. Covers auto-layout, component variants, accessible typography, and exporting developer specs.",
                "proficiency_level": "beginner",
                "duration_minutes": 30,
                "preparation_effort": 1,
                "interaction_mode": "online",
                "location_details": "Google Meet",
            },
            {
                "email": "maya@skillswap.edu",
                "cat_slug": "programming",
                "title": "Advanced Data Structures & Graph Algorithms in Python",
                "description": "In-depth review of graph traversal (BFS/DFS), Dijkstra's shortest path, dynamic programming, and asymptotic time complexity for technical coding interviews.",
                "proficiency_level": "advanced",
                "duration_minutes": 60,
                "preparation_effort": 2,
                "interaction_mode": "online",
                "location_details": "Discord Voice / Screen Share",
            },
        ]

        for off in sample_offers:
            author = users_map.get(off["email"])
            cat = categories_map.get(off["cat_slug"])
            if author and cat:
                existing = SkillOffer.query.filter_by(user_id=author.id, title=off["title"]).first()
                if not existing:
                    points, difficulty, breakdown = scoring_service.calculate_points(
                        duration_minutes=off["duration_minutes"],
                        proficiency_level=off["proficiency_level"],
                        prep_effort=off["preparation_effort"],
                    )
                    offer_obj = SkillOffer(
                        user_id=author.id,
                        category_id=cat.id,
                        title=off["title"],
                        description=off["description"],
                        proficiency_level=off["proficiency_level"],
                        duration_minutes=off["duration_minutes"],
                        preparation_effort=off["preparation_effort"],
                        interaction_mode=off["interaction_mode"],
                        location_details=off["location_details"],
                        difficulty=difficulty,
                        suggested_points=points,
                        scoring_breakdown_json=json.dumps(breakdown),
                        is_active=True,
                    )
                    db.session.add(offer_obj)
                    print(f"[+] Seeded Offer: '{offer_obj.title}' -> {points} pts ({difficulty})")

        # 5. Seed Sample Skill Request
        ethan = users_map.get("ethan@skillswap.edu")
        cs_cat = categories_map.get("programming")
        if ethan and cs_cat:
            existing_req = SkillRequest.query.filter_by(user_id=ethan.id, title="Help with Python Backend & Database Models").first()
            if not existing_req:
                req = SkillRequest(
                    user_id=ethan.id,
                    category_id=cs_cat.id,
                    title="Help with Python Backend & Database Models",
                    description="I have a math modeling project that needs a clean SQLite/PostgreSQL backend in Python. Looking for guidance on setting up SQLAlchemy relations.",
                    desired_level="intermediate",
                    preferred_duration_minutes=60,
                    interaction_mode="hybrid",
                    budget_points=35.0,
                    is_open=True,
                )
                db.session.add(req)
                print(f"[+] Seeded Request: '{req.title}' by {ethan.full_name}")

        db.session.commit()
        print("[SUCCESS] SkillSwap database successfully seeded!")


if __name__ == "__main__":
    seed_database()
