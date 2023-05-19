from pathlib import Path
from os import remove as remove_file
from subprocess import run as run_subprocess

from trimesh.exchange.obj import export_obj
from trimesh.base import Trimesh

from foam.model import *
from foam.utility import *

EXTERNAL_BINARY_DIR = Path(__file__).parent
MAKE_TREE_MEDIAL_PATH = EXTERNAL_BINARY_DIR / "makeTreeMedial"
MAKE_TREE_GRID_PATH = EXTERNAL_BINARY_DIR / "makeTreeGrid"
MAKE_TREE_HUBBARD_PATH = EXTERNAL_BINARY_DIR / "makeTreeHubbard"
MAKE_TREE_OCTREE_PATH = EXTERNAL_BINARY_DIR / "makeTreeOctree"
MAKE_TREE_SPAWN_PATH = EXTERNAL_BINARY_DIR / "makeTreeSpawn"
MANIFOLD_PATH = EXTERNAL_BINARY_DIR / "manifold"
SIMPLIFY_PATH = EXTERNAL_BINARY_DIR / "simplify"


def read_spherization_file(filename: Path, offset: NDArray) -> list[Spherization]:
    output = []
    with open(filename, 'r') as output_spheres:
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
            output.append(Spherization(spheres, mean, best, worst))

    return output


def compute_medial_spheres(
        mesh: Trimesh,
        depth: int = 1,
        branch: int = 8,
        tester_level: int = 2,
        num_cover: int = 10000,
        min_cover: int = 1,
        init_spheres: int = 1000,
        min_spheres: int = 200,
        er_fact: int = 2,
        expand: bool = True,
        merge: bool = True,
        optimize: bool = True,
        optimization_level: int = 1
    ) -> list[Spherization]:

    _ = mesh.vertex_normals    # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        output_file = input_path.parent / (input_path.stem + '-medial.sph')

        command = [
            str(Path(__file__).parent / 'makeTreeMedial'),
            '-nopause',
            '-verify',
            '-branch',
            str(branch),
            '-depth',
            str(depth),
            '-testerLevels',
            str(tester_level),
            '-numCover',
            str(num_cover),
            '-minCover',
            str(min_cover),
            '-initSpheres',
            str(init_spheres),
            '-minSpheres',
            str(min_spheres),
            '-erFact',
            str(er_fact),
            '-maxOptLevel',
            str(optimization_level),
            str(input_path),
            ]

        if expand:
            command.append('-expand')
        if merge:
            command.append('-merge')
        if optimize:
            command.extend(['-optimise', 'simplex'])

        run_subprocess(command)

    if not output_file.exists:
        raise RuntimeError("Failed to create spheres for mesh. Mesh is probably invalid.")

    low_bounds, high_bounds = mesh.bounds
    offset = (high_bounds + low_bounds) / 2

    spheres = read_spherization_file(output_file, offset)
    remove_file(output_file)

    return spheres
