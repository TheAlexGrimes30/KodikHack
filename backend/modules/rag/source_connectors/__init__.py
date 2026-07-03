from backend.modules.rag.source_connectors.base import SourceConnector
from backend.modules.rag.source_connectors.cbr import CBRSourceConnector
from backend.modules.rag.source_connectors.competitor_pages import CompetitorPagesConnector
from backend.modules.rag.source_connectors.local_folder import LocalFolderConnector
from backend.modules.rag.source_connectors.rosstat import RosstatSourceConnector
from backend.modules.rag.source_connectors.vc_articles import VCArticlesConnector

__all__ = [
    "SourceConnector",
    "CBRSourceConnector",
    "CompetitorPagesConnector",
    "LocalFolderConnector",
    "RosstatSourceConnector",
    "VCArticlesConnector",
]
