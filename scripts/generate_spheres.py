from json import dumps
from pathlib import Path

from fire import Fire
from foam import *


def main(
        mesh: str,
        output: str | None = None,
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000,
        simplify_ratio: float = 0.2
    ):
    mesh_filepath = Path(mesh)
    if not mesh_filepath.exists:
        raise RuntimeError(f"Path {mesh} does not exist!")

    loaded_mesh = load_mesh_file(mesh_filepath)

    spheres = spherize_mesh(
        loaded_mesh,
        spherization_kwargs = {
            'depth': depth,
            'branch': branch,
            },
        process_kwargs = {
            'manifold_leaves': manifold_leaves,
            'ratio': simplify_ratio,
            },
        )

    if not output:
        output = mesh_filepath.stem + "-spheres.json"

    with open(output, 'w') as f:
        f.write(dumps(spheres, indent = 4, cls = SphereEncoder))


if __name__ == "__main__":
    Fire(main)
