from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from trimesh.base import Trimesh
from trimesh.scene.scene import Scene
from trimesh.util import concatenate


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
