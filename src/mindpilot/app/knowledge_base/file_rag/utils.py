from .retrievers import (
    BaseRetrieverService,
    EnsembleRetrieverService,
    VectorstoreRetrieverService,
)

Retrivals = {
    "vectorstore": VectorstoreRetrieverService,
    "ensemble": EnsembleRetrieverService,
}


def get_Retriever(type: str = "vectorstore") -> BaseRetrieverService:
    return Retrivals[type]
