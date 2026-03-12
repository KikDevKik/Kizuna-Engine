import json
import logging
from google.cloud import firestore
from google.auth.exceptions import DefaultCredentialsError

logger = logging.getLogger(__name__)

class FirestoreService:
    def __init__(self):
        self.client = None
        self.fallback_mode = False
        try:
            self.client = firestore.AsyncClient()
            logger.info("FirestoreService initialized in GCP mode.")
        except DefaultCredentialsError:
            self.fallback_mode = True
            logger.warning("FirestoreService initialized in fallback mode (no GCP credentials).")
        except Exception as e:
            self.fallback_mode = True
            logger.error(f"Failed to initialize FirestoreService, using fallback mode. Error: {e}")

    async def get_agent(self, user_id: str, agent_id: str) -> dict | None:
        if self.fallback_mode:
            return None
        doc_ref = self.client.collection("users").document(user_id).collection("agents").document(agent_id)
        doc = await doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    async def save_agent(self, user_id: str, agent_id: str, data: dict) -> None:
        if self.fallback_mode:
            return
        doc_ref = self.client.collection("users").document(user_id).collection("agents").document(agent_id)
        await doc_ref.set(data)

    async def list_agents(self, user_id: str) -> list[dict]:
        if self.fallback_mode:
            return []
        agents_ref = self.client.collection("users").document(user_id).collection("agents")
        docs = agents_ref.stream()
        return [doc.to_dict() async for doc in docs]

    async def delete_agent(self, user_id: str, agent_id: str) -> None:
        if self.fallback_mode:
            return
        doc_ref = self.client.collection("users").document(user_id).collection("agents").document(agent_id)
        await doc_ref.delete()

    async def get_chronicle(self, user_id: str, agent_id: str) -> dict | None:
        if self.fallback_mode:
            return None
        doc_ref = self.client.collection("users").document(user_id).collection("chronicle").document(agent_id)
        doc = await doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    async def save_chronicle(self, user_id: str, agent_id: str, data: dict) -> None:
        if self.fallback_mode:
            return
        doc_ref = self.client.collection("users").document(user_id).collection("chronicle").document(agent_id)
        await doc_ref.set(data)

    async def delete_chronicle(self, user_id: str, agent_id: str) -> None:
        if self.fallback_mode:
            return
        doc_ref = self.client.collection("users").document(user_id).collection("chronicle").document(agent_id)
        await doc_ref.delete()

firestore_service = FirestoreService()
