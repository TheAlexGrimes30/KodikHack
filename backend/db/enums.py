import enum


class ProjectStage(str, enum.Enum):
    IDEA = "idea"
    MVP = "mvp"
    EARLY_REVENUE = "early_revenue"
    GROWTH = "growth"

class RiskAppetite(str, enum.Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"

class Reversibility(str, enum.Enum):
    CHEAP_REVERSIBLE = "cheap_reversible"
    COSTLY_REVERSIBLE = "costly_reversible"
    COSTLY_IRREVERSIBLE = "costly_irreversible"

class ThresholdVerdict(str, enum.Enum):
    SCALE = "scale"
    HOLD = "hold"
    EXIT = "exit"
    PROBE = "probe"

class SessionStatus(str, enum.Enum):
    DRAFT = "draft"
    ANALYZED = "analyzed"
    ACTED = "acted"
    CLOSED = "closed"

class AgentKind(str, enum.Enum):
    ENVIRONMENT = "environment"
    DESTRUCTOR = "destructor"

class FeedMode(str, enum.Enum):
    STREAM = "stream"
    BATCH = "batch"
