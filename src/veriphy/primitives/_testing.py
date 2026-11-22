"""Help a pack test its own primitives: the same input and seed must give the same output."""

from veriphy.core import PrimitiveError
from veriphy.primitives._registry import Registry


def assert_deterministic(registry: Registry, name: str, inputs: dict[str, object]) -> dict[str, object]:
    """Call a primitive twice on the same input and raise unless both outputs are equal.

    Args:
        registry: The registry holding the primitive.
        name: The primitive's name.
        inputs: Its input, with its seed when it is random.

    Returns:
        The output.

    Raises:
        PrimitiveError: If the two outputs differ, naming the first key that does.
    """
    first, second = registry.call(name, inputs), registry.call(name, inputs)
    if first == second:
        return first
    differing = sorted(k for k in set(first) | set(second) if first.get(k) != second.get(k))
    message = f'{name} is not deterministic: two calls on the same input differ in {", ".join(differing)}'
    raise PrimitiveError(message)
