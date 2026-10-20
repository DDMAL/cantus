from prometheus_client import REGISTRY

BROWSER = "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"


def sample(name: str, **labels: str) -> float:
    """The current value of one series in the default registry, 0 if unset."""
    return REGISTRY.get_sample_value(name, labels) or 0.0
