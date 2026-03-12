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

    _JSON_FIELDS = [
        "traits", "known_languages", "neural_signature",
        "identity_anchors", "affinity_matrix", "emotional_state",
    ]

    def _deserialize_agent(self, data: dict) -> dict:
        """Parse any JSON-string fields back to their native Python types."""
        for field in self._JSON_FIELDS:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = json.loads(data[field])
                except Exception:
                    pass
        return data

    async def get_agent(self, user_id: str, agent_id: str) -> dict | None:
        if self.fallback_mode:
            return None
        doc_ref = self.client.collection("users").document(user_id).collection("agents").document(agent_id)
        doc = await doc_ref.get()
        if doc.exists:
            return self._deserialize_agent(doc.to_dict())
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
        return [self._deserialize_agent(doc.to_dict()) async for doc in docs]

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
