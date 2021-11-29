import pkg_resources

from dataclasses import make_dataclass, field


def identity_factory(klass):
    return klass


def registry_factory(
    entry_point,
    make_display_name=None,
    validator=None,
    entrypoint_factory=identity_factory,
):
    """Create a registry of entry-point methods.

    Args:
        entry_point (str):  Name of python entrypoint to load, e.g. "deal.parsers.live"
        make_display_name (function, optional): callable[str]
        validator (function, optional): callable[entry_point] - raises an exception if EntryPoint doesn't meet some validation
        entrypoint_factory (function, optional): callable[entry_point] - preprocesses an entrypoint (e.g. for dynamic inheritance)
    Returns:
        Registry - An entrypoint registry that enables lookups by entrypoint names,
    """

    entry_points = [ep for ep in pkg_resources.iter_entry_points(entry_point)]

    if callable(validator):
        for ep in entry_points:
            validator(ep.load())  # validator should raise

    Registry = make_dataclass(
        "EntryPointRegistry",
        [
            (ep.name, "typing.Callable", field(default=entrypoint_factory(ep.load())))
            for ep in entry_points
        ],
        frozen=True,
        namespace={
            "get": classmethod(lambda cls, name: getattr(cls, name)),
            "entrypoints": [ep.name for ep in entry_points],
        },
    )
    return Registry
