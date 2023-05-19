from collections import defaultdict
from itertools import chain
from pathlib import Path
import xmltodict
from concurrent.futures import ThreadPoolExecutor, wait

from fire import Fire
from foam import *


def generate_spheres(
        mesh_filename: Path,
        scale: NDArray | None,
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000
    ) -> Spherization:
    loaded_mesh = load_mesh_file(mesh_filename)

    if scale is not None:
        loaded_mesh.apply_scale(scale)

    if not check_valid_for_spherization(loaded_mesh):
        loaded_mesh = manifold(loaded_mesh, manifold_leaves)
        smooth_mesh(loaded_mesh)

    if not check_valid_for_spherization(loaded_mesh):
        raise RuntimeError("Failed to make mesh valid!")

    try:
        spheres = compute_medial_spheres(loaded_mesh, depth = depth, branch = branch)
    except:
        loaded_mesh = manifold(loaded_mesh, manifold_leaves)
        smooth_mesh(loaded_mesh)
        spheres = compute_medial_spheres(loaded_mesh, depth = depth, branch = branch)

    return spheres[-1]


def main(
        filename: str = "assets/panda/panda.urdf",
        depth: int = 1,
        branch: int = 8,
        manifold_leaves: int = 1000,
        threads: int = 32
    ):
    path = Path(filename).parent

    with open(filename, 'r') as f:
        urdf = xmltodict.parse(f.read())

    executor = ThreadPoolExecutor(max_workers = threads)
    name_to_future = defaultdict(list)
    for link in urdf['robot']['link']:
        name = link['@name']
        if 'collision' not in link:
            continue

        collision = link['collision']  # TODO: Assumes one collision geometry right now
        geometry = collision['geometry']
        print(geometry)

        if 'mesh' in geometry:
            mesh = geometry['mesh']
            mesh_filename = mesh['@filename']
            scale = np.array(mesh['@scale']) if 'scale' in mesh else None

            name_to_future[name].append(
                executor.submit(
                    generate_spheres, path / mesh_filename, scale, depth, branch, manifold_leaves
                    )
                )

    wait(list(chain(*name_to_future.values())))

    for link in urdf['robot']['link']:
        name = link['@name']
        if 'collision' not in link:
            continue

        collision = link['collision']                                                      # TODO: Assumes one collision geometry right now
        if name in name_to_future:
            collision = []
            for future in name_to_future[name]:
                spherization = future.result()
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
