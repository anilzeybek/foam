from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from numpy.typing import NDArray

from trimesh.base import Trimesh
from trimesh.scene.scene import Scene
from trimesh.util import concatenate
from trimesh.exchange.load import load_mesh
from trimesh.repair import *
from trimesh.smoothing import filter_humphrey, filter_taubin

import numpy as np

import xmltodict

def fix_mesh(mesh: Trimesh):
    fix_normals(mesh)
    fix_inversion(mesh)
    fix_winding(mesh)
    mesh.vertex_normals = -mesh.vertex_normals

def smooth_mesh(mesh: Trimesh):
    filter_humphrey(mesh, iterations=100)

@contextmanager
def tempmesh():
    f = NamedTemporaryFile('w', suffix = f'.obj')
    try:
        yield f, Path(f.name)
    finally:
        f.close()


def as_mesh(scene_or_mesh: Trimesh | Scene) -> Trimesh | None:
    if isinstance(scene_or_mesh, Scene):
        if len(scene_or_mesh.geometry) == 0:
            return None
        else:
            return concatenate(
                [Trimesh(vertices = g.vertices, faces = g.faces) for g in scene_or_mesh.geometry.values()]
                )                                                                                          # type: ignore
    else:
        return scene_or_mesh


def load_mesh_file(mesh_filepath: Path) -> Trimesh:
    try:
        mesh = as_mesh(load_mesh(mesh_filepath, process = False))   # type: ignore
        if mesh is None:
            raise RuntimeError("Failed to load mesh!")

        return mesh

    except Exception as e:
        raise e

@dataclass
class URDFMesh:
    name:str
    filepath: Path
    xyz: NDArray
    rpy: NDArray
    scale: NDArray

URDFDict = dict[str, Any]

def _urdf_array_to_np(array: str) -> NDArray:
    return np.fromiter(map(float, array.split()), dtype = float)

def _urdf_clean_filename(filename: str) -> str:
    if filename.startswith('package://'):
        filename = filename[len('package://'):]

    return filename

def load_urdf(urdf_path: Path) -> URDFDict:
    with open(urdf_path, 'r') as f:
        xml = xmltodict.parse(f.read())
        xml['robot']['@path'] = urdf_path
        return xml

def get_urdf_meshes(urdf:  URDFDict)-> list[URDFMesh]:
    urdf_dir = Path(urdf['robot']['@path']).parent

    meshes = []
    for link in urdf['robot']['link']:
        name = link['@name']
        if 'collision' not in link:
            continue

        # TODO: Assumes one collision geometry right now
        collision = link['collision']
        if 'origin' in collision:
            xyz = _urdf_array_to_np(collision['origin']['@xyz'])
            rpy = _urdf_array_to_np(collision['origin']['@rpy'])
        else:
            xyz = np.array([0., 0., 0.])
            rpy = np.array([0., 0., 0.])

        geometry = collision['geometry']
        if 'mesh' in geometry:
            mesh = geometry['mesh']
            filename = _urdf_clean_filename(mesh['@filename'])
            scale = _urdf_array_to_np(mesh['@scale']) if 'scale' in mesh else np.array([1., 1., 1.])

            meshes.append(URDFMesh(name, urdf_dir / filename, xyz, rpy, scale))

    return meshes

def set_urdf_spheres(urdf: URDFDict, spheres):
    for link in urdf['robot']['link']:
        name = link['@name']
        if 'collision' not in link:
            continue

        # TODO: Assumes one collision geometry right now
        geometry = link['collision']['geometry']
        if 'mesh' in geometry:
            collision = []
            spherization = spheres[name]
            for sphere in spherization.spheres:
                collision.append(
                    {
                        'geometry': {
                            'sphere': {
                                '@radius': sphere.radius
                                }
                            },
                        'origin': {
                            '@xyz': ' '.join(map(str, sphere.origin)), '@rpy': '0 0 0'
                            }
                        }
                    )
                link['collision'] = collision

def save_urdf(urdf: URDFDict, filename: Path):
    with open(filename, 'w') as f:
        f.write(xmltodict.unparse(urdf, pretty = True))
