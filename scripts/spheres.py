from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from fire import Fire
from trimesh import Scene, Trimesh, load_mesh
from trimesh.util import concatenate
from trimesh.voxel.creation import voxelize
from trimesh.voxel.ops import matrix_to_marching_cubes


@dataclass(slots=True, frozen=True)
class Sphere:
    origin: tuple[float, float, float]
    radius: float


@contextmanager
def tempfile(directory: Path | None = None,
             extension: str | None = None,
             binary: bool = False):
    file = NamedTemporaryFile(mode='wb' if binary else 'w',
                              dir=directory if directory else None,
                              suffix=f'.{extension}' if extension else None)
    path = Path(f.name)  # type: ignore
    try:
        yield file, path
    finally:
        file.close()


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


def spheretree(mesh: Trimesh) -> list[Sphere]:
    _ = mesh.vertex_normals
    with tempfile(extension='obj') as (input_mesh, input_path):
        input_mesh.write(export_obj(mesh))
        input_mesh.flush()

        subprocess.run([
            './build/spheretree/makeTreeMedial',
            '-branch',
            '8',
            '-depth',
            '3',
            '-testerLevels',
            '1',
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

        subprocess.run(['mv', input_path.stem + '-medial.sph', 'test.sph'])


def main(mesh: str):
    mesh_filepath = Path(mesh)
    if not mesh_filepath.exists:
        raise RuntimeError(f"Path {mesh} does not exist!")

    loaded_mesh = as_mesh(load_mesh(mesh_filepath,
                                    process=False))  # type: ignore
    watertight_mesh = loaded_mesh if loaded_mesh.is_watertight else make_watertight(
        loaded_mesh)

    spheres = spherize_mesh(watertight_mesh)


if __name__ == "__main__":
    Fire(main)
