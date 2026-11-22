"""Check particle-physics numbers with the field's codes: flavio's predictions, wilson's running, the PDG's values.

`prediction` recomputes an observable's Standard Model prediction with flavio, or its prediction with new-physics
Wilson coefficients, with flavio's theory uncertainty, and compares a claimed value with it. `run` runs Wilson
coefficients from one scale to another with wilson, matching between effective theories on the way. `pdg` reads a
particle's mass, width or lifetime from the PDG tables the `particle` package ships.
"""

import math

import numpy as np

# flavio's theory uncertainty is a Monte Carlo over its parameters: a fixed seed and sample size make it repeatable
SAMPLES = 100


def _coefficients(inputs: dict[str, object]) -> dict[str, float]:
    """Return the Wilson coefficients given as `name=value` texts."""
    given = inputs.get('coefficients')
    pairs = [str(c).split('=', 1) for c in given] if isinstance(given, list) else []
    return {name.strip(): float(value) for name, value in pairs}


def _arguments(inputs: dict[str, object]) -> tuple[float, ...]:
    """Return an observable's arguments, such as a q² bin given as `1.1,6`."""
    return tuple(float(a) for a in str(inputs.get('arguments') or '').split(',') if a.strip())


def _half_unit(value: object) -> float:
    """Return half a unit in the last digit a number was reported with."""
    text = str(value).lower()
    mantissa, _, exponent = text.partition('e')
    decimals = len(mantissa.split('.', 1)[1]) if '.' in mantissa else 0
    return 0.5 * 10.0 ** (int(exponent or 0) - decimals)


def _compare(found: float, uncertainty: float, inputs: dict[str, object]) -> dict[str, object]:
    """Compare a claimed value with a found one, within `sigmas` combined uncertainties and the claim's rounding."""
    claimed = float(str(inputs['claimed']))
    claimed_uncertainty = float(str(inputs.get('uncertainty') or 0))
    sigmas = float(str(inputs.get('sigmas') or 2))
    tolerance = sigmas * math.hypot(uncertainty, claimed_uncertainty) + _half_unit(inputs['claimed'])
    return {
        'status': 'agrees' if abs(found - claimed) <= tolerance else 'differs',
        'compared': {'field': 'value', 'found': found, 'claimed': claimed, 'tolerance': tolerance},
    }


def prediction(inputs: dict[str, object]) -> dict[str, object]:
    """Recompute an observable's prediction with flavio, and compare a claimed value with it.

    Args:
        inputs: `observable`, flavio's name for it (`BR(Bs->mumu)`), `arguments` (`1.1,6` for a q² bin), `claimed`,
            and optionally the claim's `uncertainty`, `sigmas` (2 by default), and new-physics `coefficients`
            (`C10_bsmumu=-1`) at `scale` (4.8 GeV) in `eft` (`WET`) and `basis` (`flavio`).

    Returns:
        `agrees` when the claim is within `sigmas` combined uncertainties of flavio's prediction, `differs` otherwise,
        with the prediction and its uncertainty.
    """
    import flavio  # noqa: PLC0415 - the pack's optional library, imported only when the check runs
    import wilson  # noqa: PLC0415

    observable, arguments, coefficients = str(inputs['observable']), _arguments(inputs), _coefficients(inputs)
    if observable not in flavio.classes.Observable.instances:
        close = [n for n in flavio.classes.Observable.instances if observable.lower()[:6] in n.lower()][:5]
        error = f"flavio has no observable '{observable}'; close names: {', '.join(close)}"
        return {'status': 'failed', 'error': error}
    np.random.seed(0)
    if coefficients:
        scale = float(str(inputs.get('scale') or 4.8))
        eft, basis = str(inputs.get('eft') or 'WET'), str(inputs.get('basis') or 'flavio')
        point = wilson.Wilson(coefficients, scale=scale, eft=eft, basis=basis)
        value = flavio.np_prediction(observable, point, *arguments)
        uncertainty = flavio.np_uncertainty(observable, point, *arguments, N=SAMPLES)
    else:
        value = flavio.sm_prediction(observable, *arguments)
        uncertainty = flavio.sm_uncertainty(observable, *arguments, N=SAMPLES)
    tools = [{'name': 'flavio', 'version': flavio.__version__, 'pin': 'version'}]
    found = {'value': float(value), 'uncertainty': float(uncertainty), 'tools': tools}
    return found | _compare(float(value), float(uncertainty), inputs)


def run(inputs: dict[str, object]) -> dict[str, object]:
    """Run Wilson coefficients from one scale to another with wilson, and return one of them there.

    Args:
        inputs: `coefficients` (`lq1_2223=1e-8`) at `scale` in `eft` and `basis`, and the `coefficient` to return at
            `to_scale` in `to_eft` and `to_basis` (the same theory and basis by default).

    Returns:
        The coefficient's real and imaginary parts at the new scale.
    """
    import wilson  # noqa: PLC0415 - the pack's optional library, imported only when the check runs

    eft, basis = str(inputs['eft']), str(inputs['basis'])
    point = wilson.Wilson(_coefficients(inputs), scale=float(str(inputs['scale'])), eft=eft, basis=basis)
    to_eft, to_basis = str(inputs.get('to_eft') or eft), str(inputs.get('to_basis') or basis)
    ran = point.match_run(scale=float(str(inputs['to_scale'])), eft=to_eft, basis=to_basis)
    name = str(inputs['coefficient'])
    # the result holds the coefficients that are not zero; the basis names every one it has
    if name not in wilson.wcxf.Basis[to_eft, to_basis].all_wcs:
        return {'status': 'failed', 'error': f"{to_eft} in the {to_basis} basis has no coefficient '{name}'"}
    value = complex(ran.dict.get(name, 0))
    tools = [{'name': 'wilson', 'version': wilson.__version__, 'pin': 'version'}]
    return {'status': 'reported', 'value': value.real, 'imaginary': value.imag, 'tools': tools}


PROPERTIES = {'mass': ('mass', 'MeV'), 'width': ('width', 'MeV'), 'lifetime': ('lifetime', 'ns')}


def pdg(inputs: dict[str, object]) -> dict[str, object]:
    """Read a particle's mass, width or lifetime from the PDG tables, and compare a claimed value with it.

    Args:
        inputs: `particle`, its PDG name (`B(s)0`, `mu-`) or Monte Carlo number (`531`), `property` (mass and width
            in MeV, lifetime in ns), `claimed`, and optionally the claim's `uncertainty` and `sigmas` (2 by default).

    Returns:
        `agrees` when the claim is within `sigmas` combined uncertainties of the PDG value, `differs` otherwise.

    Examples:
        >>> pdg({'particle': 'mu-', 'property': 'mass', 'claimed': '105.658'})['status']
        'agrees'
    """
    import particle  # noqa: PLC0415 - the pack's optional library, imported only when the check runs

    name, wanted = str(inputs['particle']), str(inputs['property'])
    if wanted not in PROPERTIES:
        return {'status': 'failed', 'error': f"the property '{wanted}' is not one of {', '.join(PROPERTIES)}"}
    try:
        found = particle.Particle.from_pdgid(int(name)) if name.lstrip('-').isdigit() else None
        found = found or particle.Particle.from_name(name)
    except (particle.ParticleNotFound, particle.InvalidParticle):
        close = [p.name for p in particle.Particle.finditer(name.split('(', maxsplit=1)[0])][:5]
        error = f"the PDG tables have no particle '{name}'; close names: {', '.join(close)}"
        return {'status': 'failed', 'error': error}
    attribute, unit = PROPERTIES[wanted]
    value = getattr(found, attribute)
    if value is None:
        return {'status': 'failed', 'error': f'the PDG tables give no {wanted} for {found.name}'}
    if wanted == 'lifetime':
        uncertainty = 0.0
    else:
        upper, lower = getattr(found, f'{attribute}_upper') or 0.0, getattr(found, f'{attribute}_lower') or 0.0
        uncertainty = max(float(upper), float(lower))
    tools = [{'name': 'particle', 'version': particle.__version__, 'pin': 'version'}]
    reported = {'particle': found.name, 'value': float(value), 'unit': unit, 'uncertainty': uncertainty, 'tools': tools}
    return reported | _compare(float(value), uncertainty, inputs)
