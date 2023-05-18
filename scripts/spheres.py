from json import dumps
from os import remove
from pathlib import Path
from subprocess import run

from fire import Fire
from trimesh.exchange.load import load_mesh
from trimesh.exchange.obj import export_obj
from trimesh.voxel.creation import voxelize
from trimesh.voxel.ops import matrix_to_marching_cubes

from common import *


def main(mesh: str,
         output: str | None = None,
         resolution: float = 0.01,
         depth: int = 1,
         branch: int = 8,
         tester_level: int = 2):
    mesh_filepath = Path(mesh)
    if not mesh_filepath.exists:
        raise RuntimeError(f"Path {mesh} does not exist!")

    loaded_mesh = as_mesh(load_mesh(mesh_filepath,
                                    process=False))  # type: ignore

    if not loaded_mesh.is_watertight:
        voxels = voxelize(loaded_mesh, resolution)
        voxels.fill()
        watertight_mesh = matrix_to_marching_cubes(voxels.matrix, resolution)
    else:
        watertight_mesh = loaded_mesh

    _ = watertight_mesh.vertex_normals  # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(watertight_mesh))
        input_mesh.flush()

        run([
            '../build/spheretree/makeTreeMedial',
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
            '-optimise',
            'simplex',
            '-maxOptLevel',
            '1',
            str(input_path)
        ])

        output_file = input_path.parent / (input_path.stem + '-medial.sph')

        low_bounds, high_bounds = loaded_mesh.bounds
        offset = (high_bounds + low_bounds) / 2

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
                    Sphere(*list(map(float, line.split()))[:-1], offset)  # type: ignore
                    for line in lines[start:start + level]
                ]

                spheres = list(filter(lambda s: s.radius > 0, spheres))

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
