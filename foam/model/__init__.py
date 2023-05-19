from dataclasses import dataclass
from json import JSONEncoder, JSONDecoder

import numpy as np
from numpy.typing import NDArray


@dataclass(slots = True)
class Sphere:
    origin: NDArray
    radius: float

    def __init__(self, x: float, y: float, z: float, r: float, offset: NDArray | None = None):
        self.origin = np.array([x, y, z])
        if offset is not None:
            self.origin += offset

        self.radius = r


class SphereEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Sphere):
            return {'origin': obj.origin, 'radius': obj.radius}

        return JSONEncoder.default(self, obj)


class SphereDecoder(JSONDecoder):

    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook = self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if 'origin' in dct and 'radius' in dct:
            return Sphere(*dct['origin'], dct['radius']) # type: ignore
        return dct


@dataclass(slots = True)
class Spherization:
    spheres: list[Sphere]
    mean_error: float
    best_error: float
    worst_error: float

    def __len__(self):
        return len(self.spheres)
