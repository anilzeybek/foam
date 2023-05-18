from json import load as jsload

import random
from fire import Fire
from trimesh.creation import icosphere
from trimesh.exchange.load import load_mesh
from trimesh.transformations import translation_matrix
from trimesh.viewer import SceneViewer
import matplotlib as mpl

from common import *


def main(mesh: str | None = None, spheres: str | None = None, level: int = 1):
    scene = Scene()
    if mesh:
        mesh_filepath = Path(mesh)
        if not mesh_filepath.exists:
            raise RuntimeError(f"Path {mesh} does not exist!")

        loaded_mesh = as_mesh(load_mesh(mesh_filepath,
                                        process=False))  # type: ignore

        scene.add_geometry(loaded_mesh)

    if spheres:
        sphere_filepath = Path(spheres)
        if not sphere_filepath.exists:
            raise RuntimeError(f"Path {spheres} does not exist!")

        with open(sphere_filepath, 'r') as json_file:
            data = jsload(json_file, cls=SphereDecoder)

        if level > len(data):
            raise RuntimeError(
                f"Level {level} greater than available ({len(data)})!")
        sphere_data = data[level]['spheres']

        cm = mpl.colormaps['viridis']
        for sphere in sphere_data:
            sphere_mesh = icosphere(radius=sphere.radius)
            sphere_mesh.visual.face_colors = [255 * c for c in cm(random.uniform(0, 1))][:3] + [50]
            scene.add_geometry(sphere_mesh,
                               transform=translation_matrix(sphere.origin))

    if mesh or spheres:
        SceneViewer(scene)


if __name__ == "__main__":
    Fire(main)
