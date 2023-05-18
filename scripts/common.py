from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from json import JSONEncoder, JSONDecoder

from trimesh.scene.scene import Scene
from trimesh.base import Trimesh
from trimesh.util import concatenate


@dataclass(slots=True)
class Sphere:
    origin: tuple[float, float, float]
    radius: float

    def __init__(self,
                 x: float,
                 y: float,
                 z: float,
                 r: float,
                 offset: list[float] | None = None):
        if offset is not None:
            self.origin = (x + offset[0], y + offset[1], z + offset[2])
        else:
            self.origin = (x, y, z)

        self.radius = r


class SphereEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Sphere):
            return {'origin': obj.origin, 'radius': obj.radius}

        return JSONEncoder.default(self, obj)


class SphereDecoder(JSONDecoder):

    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self,
                             object_hook=self.object_hook,
                             *args,
                             **kwargs)

    def object_hook(self, dct):
        if 'origin' in dct and 'radius' in dct:
            return Sphere(*dct['origin'], dct['radius'])  # type: ignore
        return dct


@contextmanager
def tempmesh():
    f = NamedTemporaryFile('w', suffix=f'.obj')
    try:
        yield f, Path(f.name)
    finally:
        f.close()


def as_mesh(scene_or_mesh: Trimesh | Scene) -> Trimesh:
    if isinstance(scene_or_mesh, Scene):
        if len(scene_or_mesh.geometry) == 0:
            raise RuntimeError("Opened an empty mesh file!")
        else:
            return concatenate(
                tuple(
                    Trimesh(vertices=g.vertices, faces=g.faces)
                    for g in scene_or_mesh.geometry.values()))  # type: ignore
    else:
        return scene_or_mesh
