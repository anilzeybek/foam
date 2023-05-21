from sys import stdout
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path

import xmltodict
from fire import Fire
from foam import *
from numpy import fromiter


def generate_spheres(
        mesh_filename: Path,
        scale: NDArray | None,
        position: NDArray | None,
        orientation: NDArray | None,
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000,
        simplify_ratio: float = 0.2
    ) -> Spherization:
    loaded_mesh = load_mesh_file(mesh_filename)

    spheres = spherize_mesh(
        loaded_mesh,
        scale,
        position,
        orientation,
        {
            'depth': depth,
            'branch': branch,
            },
        {
            'manifold_leaves': manifold_leaves,
            'ratio': simplify_ratio,
            },
        )

    return spheres[-1]


def main(
        filename: str = "assets/panda/panda.urdf",
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000,
        threads: int = 8
    ):
    path = Path(filename).parent

    with open(filename, 'r') as f:
        urdf = xmltodict.parse(f.read())

    meshes = {}
    for link in urdf['robot']['link']:
        name = link['@name']
        if 'collision' not in link:
            continue

        collision = link['collision']  # TODO: Assumes one collision geometry right now
        geometry = collision['geometry']

        position = None
        orientation = None
        if 'origin' in collision:
            position = fromiter(map(float, collision['origin']['@xyz'].split()), dtype = float)
            orientation = fromiter(map(float, collision['origin']['@rpy'].split()), dtype = float)

        if 'mesh' in geometry:
            mesh = geometry['mesh']
            mesh_filename = mesh['@filename']

            if mesh_filename.startswith('package://'):
                mesh_filename = mesh_filename[len('package://'):]

            scale = np.array(mesh['@scale']) if 'scale' in mesh else None
            meshes[name] = (mesh_filename, scale, position, orientation)

    executor = ThreadPoolExecutor(max_workers = threads)
    link_to_futures = {}

    print(f"Computing spherization for {len(meshes)} meshes...")
    for link, (mesh, scale, position, orientation) in meshes.items():
        link_to_futures[link] = executor.submit(
            generate_spheres, path / mesh, scale, position, orientation, depth, branch, manifold_leaves
            )

    wait(link_to_futures.values())

    for link in urdf['robot']['link']:
        name = link['@name']
        if 'collision' not in link:
            continue

        collision = link['collision']  # TODO: Assumes one collision geometry right now
        geometry = collision['geometry']
        if 'mesh' in geometry:
            mesh = geometry['mesh']
            mesh_filename = mesh['@filename']
            if mesh_filename.startswith('package://'):
                mesh_filename = mesh_filename[len('package://'):]

            collision = []
            spherization = link_to_futures[name].result()
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

    with open('parsed.urdf', 'w') as f:
        f.write(xmltodict.unparse(urdf, pretty = True))


if __name__ == "__main__":
    Fire(main)
