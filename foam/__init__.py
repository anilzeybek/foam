from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass
from tempfile import NamedTemporaryFile
from json import JSONEncoder, JSONDecoder
from os import remove as remove_file
from subprocess import run as run_subprocess

from trimesh.scene.scene import Scene
from trimesh.exchange.obj import export_obj
from trimesh.base import Trimesh
from trimesh.util import concatenate


@dataclass(slots = True)
class Sphere:
    origin: tuple[float, float, float]
    radius: float

    def __init__(self, x: float, y: float, z: float, r: float, offset: list[float] | None = None):
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
        JSONDecoder.__init__(self, object_hook = self.object_hook, *args, **kwargs)

    def object_hook(self, dct):
        if 'origin' in dct and 'radius' in dct:
            return Sphere(*dct['origin'], dct['radius']) # type: ignore
        return dct


@contextmanager
def tempmesh():
    f = NamedTemporaryFile('w', suffix = f'.obj')
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
                list(
                    Trimesh(vertices = g.vertices, faces = g.faces) for g in scene_or_mesh.geometry.values()
                    )
                )                                                                                            # type: ignore
    else:
        return scene_or_mesh


def compute_medial_spheres(mesh: Trimesh, depth: int = 1, branch: int = 8, tester_level: int = 2):
    _ = mesh.vertex_normals    # Need to compute vertex normals

    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        output_file = input_path.parent / (input_path.stem + '-medial.sph')

        run_subprocess(
            [
                str(Path(__file__).parent / 'makeTreeMedial'),
                '-verify',
                '-branch',
                str(branch),
                '-depth',
                str(depth),
                '-testerLevels',
                str(tester_level),
                '-numCover',
                '10000',
                '-minCover',
                '1',
                '-initSpheres',
                '1000',
                '-minSpheres',
                '200',
                '-erFact',
                '2',
                '-nopause',
                '-expand',
                '-merge',
                '-optimise',
                'simplex',
                '-maxOptLevel',
                '1',
                str(input_path),
                ]
            )

    if not output_file.exists:
        raise RuntimeError("Failed to create spheres for mesh. Mesh is probably invalid.")

    low_bounds, high_bounds = mesh.bounds
    offset = (high_bounds + low_bounds) / 2

    output = []
    with open(output_file, 'r') as output_spheres:
        lines = output_spheres.readlines()
        spheres_per_level = [int(line.split(':')[1]) for line in lines if 'Num' in line]
        best_error = [float(line.split(':')[1]) for line in lines if 'Best' in line]
        worst_error = [float(line.split(':')[1]) for line in lines if 'Worst' in line]
        mean_error = [float(line.split(':')[1]) for line in lines if 'Mean' in line]

        for i, (level, mean, best, worst) in enumerate(zip(spheres_per_level,
                                                           mean_error,
                                                           best_error,
                                                           worst_error,
                                                           strict = True)):
            start = 1 + sum(spheres_per_level[:i])
            spheres = [
                Sphere(*list(map(float, line.split()))[:-1], offset) # type: ignore
                for line in lines[start:start + level]
                ]

            spheres = list(filter(lambda s: s.radius > 0, spheres))

            output.append(
                {
                    'n_spheres': level,
                    'mean_error': mean,
                    'best_error': best,
                    'worst_error': worst,
                    'spheres': spheres
                    }
                )

    remove_file(output_file)
    return output
