from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from os import remove
from json import dumps, JSONEncoder
from subprocess import run
from fire import Fire
from trimesh.scene.scene import Scene
from trimesh.base import Trimesh
from trimesh.exchange.load import load_mesh
from trimesh.exchange.obj import export_obj
from trimesh.util import concatenate
from trimesh.voxel.creation import voxelize
from trimesh.voxel.ops import matrix_to_marching_cubes


@dataclass(slots=True)
class Sphere:
    origin: tuple[float, float, float]
    radius: float

    def __init__(self, x: float, y: float, z: float, r: float):
        self.origin = (x, y, z)
        self.radius = r


class SphereEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Sphere):
            return {'origin': obj.origin, 'radius': obj.radius}

        return JSONEncoder.default(self, obj)


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


def make_watertight(mesh: Trimesh, resolution: float = 0.01) -> Trimesh:
    voxels = voxelize(mesh, resolution)
    voxels.fill()
    return matrix_to_marching_cubes(voxels.matrix, resolution)


def main(mesh: str,
         output: str | None = None,
         depth: int = 2,
         branch: int = 10,
         tester_level: int = 1):
    mesh_filepath = Path(mesh)
    if not mesh_filepath.exists:
        raise RuntimeError(f"Path {mesh} does not exist!")

    loaded_mesh = as_mesh(load_mesh(mesh_filepath,
                                    process=False))  # type: ignore
    watertight_mesh = loaded_mesh if loaded_mesh.is_watertight else make_watertight(
        loaded_mesh)

    _ = watertight_mesh.vertex_normals  # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(watertight_mesh))
        input_mesh.flush()

        run([
            './build/spheretree/makeTreeMedial',
            '-branch',
            str(branch),
            '-depth',
            str(depth),
            '-testerLevels',
            str(tester_level),
            '-numCover',
            '10000',
            '-minCover',
            '5',
            '-initSpheres',
            '1000',
            '-minSpheres',
            '200',
            '-erFact',
            '2',
            '-nopause',
            '-expand',
            '-merge',
            str(input_path),
        ])

        output_file = input_path.parent / (input_path.stem + '-medial.sph')

        with open(output_file, 'r') as output_spheres:
            lines = output_spheres.readlines()
            spheres_per_level = [
                int(line.split(':')[1]) for line in lines if 'Num' in line
            ]

            mean_error = [
                float(line.split(':')[1]) for line in lines if 'Mean' in line
            ]

            output_json = []
            for i, (level, error) in enumerate(
                    zip(spheres_per_level, mean_error, strict=True)):
                start = 1 + sum(spheres_per_level[:i])
                spheres = [
                    Sphere(*list(map(float, line.split()))[:-1])
                    for line in lines[start:start + level]
                ]

                output_json.append({
                    'n_spheres': level,
                    'mean_error': error,
                    'spheres': spheres
                })

            if not output:
                output = mesh_filepath.stem + "-spheres.json"

            with open(output, 'w') as f:
                f.write(dumps(output_json, indent=4, cls=SphereEncoder))

        remove(output_file)


if __name__ == "__main__":
    Fire(main)
