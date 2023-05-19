from json import dumps
from pathlib import Path

from fire import Fire
from foam import *


def main(mesh: str, output: str | None = None, depth: int = 1, branch: int = 8, manifold_leaves: int = 1000):
    mesh_filepath = Path(mesh)
    if not mesh_filepath.exists:
        raise RuntimeError(f"Path {mesh} does not exist!")

    loaded_mesh = load_mesh_file(mesh_filepath)    # type: ignore

    if not check_valid_for_spherization(loaded_mesh):
        loaded_mesh = manifold(loaded_mesh, manifold_leaves)
        smooth_mesh(loaded_mesh)

    if not check_valid_for_spherization(loaded_mesh):
        raise RuntimeError("Failed to make mesh valid!")

    spheres = compute_medial_spheres(loaded_mesh, depth = depth, branch = branch)

    if not output:
        output = mesh_filepath.stem + "-spheres.json"

    with open(output, 'w') as f:
        f.write(dumps(spheres, indent = 4, cls = SphereEncoder))


if __name__ == "__main__":
    Fire(main)
