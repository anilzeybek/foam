from sys import stdout
from pathlib import Path
from os import remove as remove_file
from subprocess import run, DEVNULL

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
MANIFOLD_OLD_PATH = EXTERNAL_BINARY_DIR / "manifold_old"
SIMPLIFY_OLD_PATH = EXTERNAL_BINARY_DIR / "simplify_old"


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


def compute_spheres_helper(mesh: Trimesh, command: list[str]) -> list[Spherization]:
    _ = mesh.vertex_normals    # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        output_file = input_path.parent / (input_path.stem + '-medial.sph')
        run(command + [str(input_path)], stdout = DEVNULL)

    if not output_file.exists():
        raise RuntimeError("Failed to create spheres for mesh. Mesh is probably invalid.")

    low_bounds, high_bounds = mesh.bounds
    offset = (high_bounds + low_bounds) / 2

    spheres = read_spherization_file(output_file, offset)
    remove_file(output_file)

    return spheres


def check_valid_for_spherization(mesh: Trimesh) -> bool:
    try:
        command = [str(MAKE_TREE_MEDIAL_PATH), '-nopause', '-verify', '-depth', '0']
        compute_spheres_helper(mesh, command)
        return True
    except:
        return False


def compute_medial_spheres(
        mesh: Trimesh,
        depth: int = 1,
        branch: int = 8,
        tester_level: int = 2,
        num_cover: int = 5000,
        min_cover: int = 5,
        init_spheres: int = 500,
        min_spheres: int = 100,
        er_fact: int = 2,
        expand: bool = True,
        merge: bool = True,
        optimize: bool = True,
        optimization_level: int = 1
    ) -> list[Spherization]:

    command = [
        str(MAKE_TREE_MEDIAL_PATH),
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
        ]

    if expand:
        command.append('-expand')
    if merge:
        command.append('-merge')
    if optimize:
        command.extend(['-optimise', 'simplex'])

    return compute_spheres_helper(mesh, command)


def simplify(mesh: Trimesh, ratio: float = 0.5, aggressiveness: float = 7.0) -> Trimesh:
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run(
                [
                    str(SIMPLIFY_PATH),
                    str(input_path),
                    str(output_path),
                    str(ratio),
                    str(aggressiveness),
                    ],
                stdout = DEVNULL
                )

            return load_mesh_file(output_path)


def simplify_manifold(mesh: Trimesh, ratio: float = 0.5) -> Trimesh:
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run(
                [
                    str(SIMPLIFY_OLD_PATH),
                    '-i',
                    str(input_path),
                    '-o',
                    str(output_path),
                    '-r',
                    str(ratio),
                    ],
                stdout = DEVNULL
                )

            return load_mesh_file(output_path)


def manifold(mesh: Trimesh, leaves: int = 1000) -> Trimesh:
    _ = mesh.vertex_normals    # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run([str(MANIFOLD_OLD_PATH), str(input_path), str(output_path), str(leaves)], stdout = DEVNULL)
            return load_mesh_file(output_path)


def manifold_plus(mesh: Trimesh, depth: int = 8) -> Trimesh:
    _ = mesh.vertex_normals    # Need to compute vertex normals
    with tempmesh() as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        with tempmesh() as (_, output_path):
            run(
                [
                    str(MANIFOLD_OLD_PATH),
                    '--input',
                    str(input_path),
                    '--output',
                    str(output_path),
                    '--depth',
                    str(depth)
                    ],
                stdout = DEVNULL
                )

            return load_mesh_file(output_path)
