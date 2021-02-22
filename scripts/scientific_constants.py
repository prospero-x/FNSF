
"""
The purpose of this is so that I don't have to keep re-typing
constants for every new simulation I run.
"""

class ScientificConstant:
    """
    ScientificConstant overloads operators associated with Python3 numberic
    types, for example __truediv__ and __floordiv__ instead of __div__
    (Python2).

    Reference: https://docs.python.org/3.3/reference/datamodel.html#emulating-numeric-types
    """

    def __init__(self, name, value, units):
        self.name = name
        self.value = value
        self.units = units

    def __mul__(self, other):
        if isinstance(other, ScientificConstant):
            return self.value * other.value
        return self.value * other

    def __truediv__(self, other):
        if isinstance(other, ScientificConstant):
            return self.value / other.value
        return self.value / other

    def __pow__(self, other):
        if isinstance(other, ScientificConstant):
            raise TypeError(
                'why are you raising something to the power of a '
                + 'scientific constant?',
            )
        return self.value ** other

    def __rmul__(self, other):
        if isinstance(other, ScientificConstant):
            return other.value * self.value
        return other * self.value

    def __rtruediv__(self, other):
        if isinstance(other, ScientificConstant):
            return other.value / self.value
        return other / self.value

    def __repr__(self):
        return ('{'
            + f'"name": "{self.name}",'
            + f'"value": {self.value},'
            + f'"units": "{self.units}"'
            + '}')



eps0 = ScientificConstant('Vacuum Permittivity', 8.8541878128e-12, 'F/m')
qe = ScientificConstant('Electron Charge', 1.602176634e-19, 'C')
kB = ScientificConstant('Boltzmann Constant', 1.380649e-23, 'J/K')
amu2kg = ScientificConstant('A.M.U', 1.66053906660e-27, 'kg')

__all__ = [
    eps0,
    qe,
    kB,
    amu2kg,
]


if __name__ == '__main__':
    # Example
    print(f'eps0 * 2: {eps0 * 2}')
    print(f'eps0/qe:  {eps0/qe}')
    print(eps0)
