from pathlib import Path

from fire import Fire

from foam import *


def main(
        filename: str = "assets/panda/panda.urdf",
        output: str = "spherized.urdf",
        database: str = "sphere_database.json",
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000,
        simplification_ratio: float = 0.2,
        threads: int = 8
    ):

    sh = SpherizationHelper(Path(database), threads)

    urdf = load_urdf(Path(filename))
    meshes = get_urdf_meshes(urdf)

    for mesh in meshes:
        sh.spherize_mesh(
            mesh.name,
            mesh.filepath,
            mesh.scale,
            mesh.xyz,
            mesh.rpy,
            depth,
            branch,
            manifold_leaves,
            simplification_ratio,
            )

    spheres = {mesh.name: sh.get_spherization(mesh.name, branch, depth) for mesh in meshes}
    set_urdf_spheres(urdf, spheres)
    save_urdf(urdf, Path(output))


if __name__ == "__main__":
    Fire(main)
