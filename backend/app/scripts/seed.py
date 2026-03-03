"""
Seed script: creates demo company, user, and sample agent.
Run: python -m app.scripts.seed
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.database import Base, async_session_factory, engine
from app.core.security import hash_password
from app.models.agent import Agent
from app.models.user import Company, User


async def seed():
    # Create tables (dev only – use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as db:
        company = await db.scalar(select(Company).where(Company.slug == "demo-corp"))
        if not company:
            company = Company(name="Demo Corp", slug="demo-corp", plan="pro")
            db.add(company)
            await db.flush()

        user = await db.scalar(select(User).where(User.email == "admin@demo.com"))
        if not user:
            user = User(
                company_id=company.id,
                email="admin@demo.com",
                hashed_password=hash_password("demo1234"),
                full_name="Demo Admin",
                role="owner",
            )
            db.add(user)
        else:
            user.company_id = company.id
            user.hashed_password = hash_password("demo1234")
            user.full_name = "Demo Admin"
            user.role = "owner"
            user.is_active = True

        def agent_payload(
            name: str,
            description: str,
            system_prompt: dict,
            call_settings: dict,
            data_extraction: dict,
            phone_numbers: list | None,
        ):
            return Agent(
                company_id=company.id,
                name=name,
                description=description,
                status="active",
                system_prompt=system_prompt,
                voice_settings={
                    "provider": "elevenlabs",
                    "voiceId": "default",
                    "speed": 1.0,
                    "pitch": 0.0,
                },
                call_settings=call_settings,
                data_extraction=data_extraction,
                phone_numbers=phone_numbers,
            )

        async def upsert_agent(
            name: str,
            description: str,
            system_prompt: dict,
            call_settings: dict,
            data_extraction: dict,
            phone_numbers: list | None = None,
        ):
            existing = await db.scalar(
                select(Agent).where(Agent.company_id == company.id, Agent.name == name)
            )
            if existing:
                existing.description = description
                existing.status = "active"
                existing.system_prompt = system_prompt
                existing.voice_settings = {
                    "provider": "elevenlabs",
                    "voiceId": "default",
                    "speed": 1.0,
                    "pitch": 0.0,
                }
                existing.call_settings = call_settings
                existing.data_extraction = data_extraction
                existing.phone_numbers = phone_numbers
                return existing

            payload = agent_payload(
                name,
                description,
                system_prompt,
                call_settings,
                data_extraction,
                phone_numbers,
            )
            db.add(payload)
            return payload

        support_prompt = {
            "personality": "You are a friendly and professional customer support agent for Demo Corp.",
            "goals": [
                "Understand the customer's issue",
                "Provide clear solutions",
                "Ensure customer satisfaction",
            ],
            "environment": "Customer support center",
            "constraints": [
                "Never share confidential info",
                "Always be polite",
                "Escalate if unsure",
            ],
            "firstMessage": "Hello! Thank you for calling Demo Corp. How can I help you today?",
            "tone": "friendly",
            "language": "en",
        }

        support_agent = await upsert_agent(
            name="Support Agent",
            description="Handles customer support calls",
            system_prompt=support_prompt,
            call_settings={
                "maxDurationSeconds": 600,
                "enableRecording": True,
                "timeout": 30,
            },
            data_extraction={
                "enabled": True,
                "extractionPrompt": "Extract customer details, main issue, resolution, and sentiment from this call transcript.",
                "customServer": {"enabled": False},
                "fallbackToOpenAI": True,
                "fieldsToExtract": {
                    "customer_name": "Extract the customer's full name",
                    "email": "Extract email if mentioned",
                    "issue_category": "Categorize the main issue",
                    "issue_description": "Describe the main issue",
                    "severity": "Rate severity: low, medium, high, critical",
                    "resolution_status": "resolved, pending, or escalated",
                    "resolution_description": "What resolution was provided",
                    "next_steps": "List any follow-up actions",
                    "sentiment": "Overall sentiment: positive, neutral, negative",
                },
            },
            phone_numbers=["+1234567890"],
        )

        sales_prompt = {
            "personality": "You are an enthusiastic and knowledgeable sales representative for Demo Corp.",
            "goals": [
                "Understand the prospect's needs",
                "Present relevant products/services",
                "Schedule follow-up meetings",
            ],
            "environment": "Sales department",
            "constraints": [
                "Don't oversell",
                "Be honest about limitations",
                "Always follow up",
            ],
            "firstMessage": "Hi there! I'm from Demo Corp. I'd love to learn about your needs and see how we can help!",
            "tone": "enthusiastic",
            "language": "en",
        }

        sales_agent = await upsert_agent(
            name="Sales Agent",
            description="Handles sales inquiry calls",
            system_prompt=sales_prompt,
            call_settings={
                "maxDurationSeconds": 900,
                "enableRecording": True,
                "timeout": 30,
            },
            data_extraction={
                "enabled": True,
                "extractionPrompt": "Extract prospect details and sales-related information from this call.",
                "customServer": {"enabled": False},
                "fallbackToOpenAI": True,
                "fieldsToExtract": {
                    "prospect_name": "Extract prospect's name",
                    "company": "Extract prospect's company",
                    "email": "Extract email if mentioned",
                    "product_interest": "What products/services interested in",
                    "budget_range": "Any budget mentioned",
                    "timeline": "When do they need the solution",
                    "decision_maker": "Is this the decision maker",
                    "next_meeting": "Any follow-up meeting scheduled",
                    "close_probability": "Rate close probability: low, medium, high",
                },
            },
        )

        await db.commit()
        print("✅ Seed data ready.")
        print(f"   Company: {company.name} ({company.slug})")
        print(f"   User: {user.email} / demo1234")
        print(f"   Agents: {support_agent.name}, {sales_agent.name}")


if __name__ == "__main__":
    asyncio.run(seed())
