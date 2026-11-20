def merge_config(base, override):
    """Deep-merge override into a copy of base. Must not mutate inputs."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            base[k] = merge_config(base[k], v)
        else:
            base[k] = v
    return base
