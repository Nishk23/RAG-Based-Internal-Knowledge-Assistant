from app.config import settings
from app.storage.document_store import DocumentStore

store = DocumentStore(settings.database_url)
