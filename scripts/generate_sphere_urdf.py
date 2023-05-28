from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

import xmltodict
from fire import Fire
from foam import *
from numpy import fromiter

def main(
        filename: str = "assets/panda/panda.urdf",
        output: str = "spherized.urdf",
        database: str = "sphere_database.json",
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000,
        threads: int = 8
    ):
    ps = ParallelSpherizer(threads)
    db = SpherizationDatabase(Path(database))

    urdf = load_urdf(Path(filename))
    meshes = get_urdf_meshes(urdf)

    for mesh in meshes:
        if not db.exists(mesh.name, branch, depth):
            ps.spherize_mesh(mesh.name, mesh.filepath, mesh.scale, mesh.xyz, mesh.rpy,
                             {'depth': depth, 'branch': branch},
                             {'manifold_leaves': manifold_leaves, 'ratio': 0.2})

    ps.wait()

    spheres = {}
    for mesh in meshes:
        if not db.exists(mesh.name, branch, depth):
            spherization = ps.get(mesh.name)
            for level, sphere_level in enumerate(spherization):
                db.add(mesh.name, branch, level, sphere_level)

            spheres[mesh.name] = spherization[-1]

        else:
            spheres[mesh.name] = db.get(mesh.name, branch, depth)

    set_urdf_spheres(urdf, spheres)
    save_urdf(urdf, Path(output))

if __name__ == "__main__":
    Fire(main)
