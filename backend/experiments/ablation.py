from dataclasses import dataclass, asdict
from typing import Dict, Any, List

@dataclass(frozen=True)
class ExperimentConfig:
    """
    Represents an experimental or ablation configuration for benchmark studies.
    Enables comparing full multi-agent orchestration against ablated variants
    (e.g., without RAG, without self-correction, or single-agent baseline).
    """
    name: str
    configuration_type: str  # "multi_agent" or "single_agent"
    rag_enabled: bool
    self_correction_enabled: bool
    multi_agent: bool
    is_executable: bool
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# Defined Ablation Matrix
REGISTERED_EXPERIMENTS: Dict[str, ExperimentConfig] = {
    "multi_agent_full": ExperimentConfig(
        name="multi_agent_full",
        configuration_type="multi_agent",
        rag_enabled=True,
        self_correction_enabled=True,
        multi_agent=True,
        is_executable=True,
        description="Full multi-agent swarm orchestration with Okapi BM25 RAG and iterative Tester->Coder self-correction loop (Active/Default)."
    ),
    "multi_agent_no_rag": ExperimentConfig(
        name="multi_agent_no_rag",
        configuration_type="multi_agent",
        rag_enabled=False,
        self_correction_enabled=True,
        multi_agent=True,
        is_executable=False,
        description="Ablation study configuration: Multi-agent swarm without RAG context retrieval (Planned for controlled benchmarking)."
    ),
    "multi_agent_no_correction": ExperimentConfig(
        name="multi_agent_no_correction",
        configuration_type="multi_agent",
        rag_enabled=True,
        self_correction_enabled=False,
        multi_agent=True,
        is_executable=False,
        description="Ablation study configuration: Multi-agent swarm without iterative self-correction loop (Planned for controlled benchmarking)."
    ),
    "single_agent_baseline": ExperimentConfig(
        name="single_agent_baseline",
        configuration_type="single_agent",
        rag_enabled=False,
        self_correction_enabled=False,
        multi_agent=False,
        is_executable=False,
        description="Benchmark baseline: Single LLM agent without multi-agent dynamic routing or iterative self-correction. Reserved for future controlled benchmarking."
    )
}

def get_registered_experiments() -> List[Dict[str, Any]]:
    """Returns a list of all registered experiment and ablation configurations."""
    return [config.to_dict() for config in REGISTERED_EXPERIMENTS.values()]

def get_active_configuration() -> ExperimentConfig:
    """Returns the currently active and executable configuration."""
    return REGISTERED_EXPERIMENTS["multi_agent_full"]

def is_configuration_executable(config_type: str) -> bool:
    """Checks whether a given configuration type is currently executable in the platform."""
    if not config_type:
        return False
    clean = config_type.strip().lower()
    return clean == "multi_agent"
