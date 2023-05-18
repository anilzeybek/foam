from contextlib import contextmanager
from dataclasses import dataclass

from tempfile import NamedTemporaryFile
from typing import TextIO
import subprocess
from pathlib import Path
from fire import Fire
from trimesh import Scene, Trimesh, load_mesh
from trimesh.util import concatenate
from trimesh.viewer import SceneViewer
from trimesh.repair import broken_faces, fill_holes, fix_inversion
from trimesh.exchange.obj import export_obj
from urdf_parser_py import urdf

from trimesh.voxel.creation import voxelize
from trimesh.voxel.ops import matrix_to_marching_cubes


def create_temp_file(directory: Path | None = None,
                     extension: str | None = None,
                     binary: bool = False) -> tuple[TextIO, Path]:
    f = NamedTemporaryFile(mode='wb' if binary else 'w',
                           dir=directory if directory else None,
                           suffix=f'.{extension}' if extension else None)
    return f, Path(f.name)  # type: ignore


@contextmanager
def tempfile(directory: Path | None = None,
             extension: str | None = None,
             binary: bool = False):
    file, path = create_temp_file(directory, extension, binary)
    try:
        yield file, path
    finally:
        file.close()


@dataclass
class Sphere:
    origin: tuple[float, float, float]
    radius: float


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


def as_mesh(scene_or_mesh: Trimesh | Scene) -> Trimesh | None:
    if isinstance(scene_or_mesh, Scene):
        if len(scene_or_mesh.geometry) == 0:
            mesh = None
        else:
            mesh = concatenate(
                tuple(
                    Trimesh(vertices=g.vertices, faces=g.faces)
                    for g in scene_or_mesh.geometry.values()))
    else:
        mesh = scene_or_mesh

    return mesh


def spherize_mesh(mesh: Trimesh) -> list[Sphere]:
    if not mesh.is_watertight:
        watertight_mesh = make_watertight(mesh)
    else:
        watertight_mesh = mesh

    spheretree(watertight_mesh)


def main(filename: str = "assets/panda/panda.urdf"):
    path = Path(filename).parent

    with open(filename, 'r') as f:
        robot = urdf.URDF.from_xml_string(f.read())

    for link in robot.links:
        name = link.name
        collisions = link.collisions

        for collision in collisions:
            geometry = collision.geometry
            origin = collision.origin

            if isinstance(geometry, urdf.Box):
                print(geometry.size)

            elif isinstance(geometry, urdf.Sphere):
                print(geometry.radius)

            elif isinstance(geometry, urdf.Cylinder):
                print(geometry.radius, geometry.length)

            elif isinstance(geometry, urdf.Mesh):
                mesh_filename: str = geometry.filename  # type: ignore
                scale = geometry.scale if geometry.scale else [1, 1, 1]
                print(mesh_filename)
                mesh = as_mesh(load_mesh(path / mesh_filename, process=False))

                if mesh:
                    spheres = spherize_mesh(mesh)

        break


if __name__ == "__main__":
    Fire(main)
