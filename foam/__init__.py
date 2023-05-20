from typing import Any

from .utility import *
from .external import *
from .model import *

from trimesh.transformations import euler_matrix, translation_matrix, quaternion_matrix


def smooth_manifold(mesh: Trimesh, manifold_leaves: int = 1000, ratio = 0.2) -> Trimesh:
    mesh = manifold(mesh, manifold_leaves)
    mesh = simplify_manifold(mesh, ratio)
    smooth_mesh(mesh)

    return mesh


def spherize_mesh(
        mesh: Trimesh,
        scale: NDArray | None = None,
        position: NDArray | None = None,
        orientation: NDArray | None = None,
        spherization_kwargs: dict[str, Any] = {},
        process_kwargs: dict[str, Any] = {}
    ) -> list[Spherization]:

    mesh = mesh.copy()

    if position is not None:
        mesh.apply_transform(translation_matrix(position))

    if orientation is not None:
        if len(orientation) == 3:
            tf = euler_matrix(*orientation, 'rxyz') # type: ignore
        elif len(orientation) == 4:
            tf = quaternion_matrix(*orientation)
        else:
            raise ValueError("Invalid orientation.")

        mesh.apply_transform(tf)

    if scale is not None:
        mesh.apply_scale(scale)

    if not check_valid_for_spherization(mesh):
        mesh = smooth_manifold(mesh, **process_kwargs)

    if not check_valid_for_spherization(mesh):
        raise RuntimeError("Failed to make mesh valid!")

    try:
        spheres = compute_medial_spheres(mesh, **spherization_kwargs)

    except:
        try:
            mesh = smooth_manifold(mesh, **process_kwargs)
            spheres = compute_medial_spheres(mesh, **spherization_kwargs)
        except:
            raise RuntimeError("Failed to process mesh.")

    return spheres
